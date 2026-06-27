import streamlit as st
import pandas as pd
import os
import tempfile
from datetime import datetime
from config import ensure_directories, COMPOSITION_DIR
import importlib
# 数据库模块动态导入
db_module = importlib.import_module('modules.database')
importlib.reload(db_module)
init_db = db_module.init_db
get_stats = db_module.get_stats
search_compositions = db_module.search_compositions
get_categories = db_module.get_categories
get_all_tags = db_module.get_all_tags
get_composition_by_id = db_module.get_composition_by_id
delete_composition = db_module.delete_composition
update_composition = db_module.update_composition
add_favorite_sentence = db_module.add_favorite_sentence
get_favorite_sentences = db_module.get_favorite_sentences
get_favorite_sentences_by_composition_id = db_module.get_favorite_sentences_by_composition_id
delete_favorite_sentence = db_module.delete_favorite_sentence
get_favorite_sentence_categories = db_module.get_favorite_sentence_categories
get_favorite_sentence_tags = db_module.get_favorite_sentence_tags
get_favorite_sentence_stats = db_module.get_favorite_sentence_stats
from modules.file_scanner import scan_composition_dir, import_single_file
from modules.analyzer import analyze_composition
from modules.file_reader import extract_title

# 动态导入避免缓存问题
llm_module = importlib.import_module('modules.llm_client')
# 强制重新加载模块
importlib.reload(llm_module)

st.set_page_config(
    page_title="我的作文管理工具",
    page_icon="📝",
    layout="wide"
)

ensure_directories()
init_db()

st.title("📝 我的作文管理工具")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 首页", "📚 作文列表", "📖 作文详情", "🌟 优秀句段收藏", "⚙️ 设置"])

# 统一的侧边栏 - 检测哪个标签页活跃并显示对应筛选
with st.sidebar:
    # 作文列表筛选（tab2）
    with st.expander("📚 作文筛选", expanded=True):
        keyword = st.text_input("关键词搜索")
        categories = [""] + get_categories()
        category = st.selectbox("分类筛选", categories)
        tags = [""] + get_all_tags()
        tag = st.selectbox("标签筛选", tags)
    
    # 优秀句段收藏筛选（tab4）
    with st.expander("🌟 句段收藏筛选", expanded=False):
        fav_categories = [""] + get_favorite_sentence_categories()
        fav_category = st.selectbox("分类筛选", fav_categories, key="fav_category")
        fav_tags_list = [""] + get_favorite_sentence_tags()
        fav_tag = st.selectbox("标签筛选", fav_tags_list, key="fav_tag")

with tab1:
    st.header("作文概览")
    
    stats = get_stats()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("作文总数", stats['total'])
    with col2:
        st.metric("平均字数", stats['avg_word_count'])
    with col3:
        st.metric("分类数量", len(stats['category_stats']))
    
    st.subheader("分类统计")
    if stats['category_stats']:
        cat_df = pd.DataFrame(
            list(stats['category_stats'].items()), columns=['分类', '数量']
        )
        st.bar_chart(cat_df.set_index('分类'))
    
    st.subheader("最近导入的作文")
    if stats['recent_compositions']:
        for comp in stats['recent_compositions']:
            with st.container():
                st.write(f"**{comp['title']}**")
                st.caption(f"分类: {comp['category']} | 字数: {comp['word_count']} | 导入时间: {comp['created_at'][:10]}")
                st.divider()
    else:
        st.info("还没有导入作文")
    
    st.divider()
    st.subheader("导入作文")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.write("📤 从本地选择文件导入（自动归档）")
        uploaded_files = st.file_uploader(
            "选择作文文件",
            type=['txt', 'docx'],
            accept_multiple_files=True
        )
        if uploaded_files:
            if st.button("📥 导入选中的文件", type="primary"):
                imported = 0
                failed = []
                for uploaded_file in uploaded_files:
                    # 保存到临时文件
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    # 导入并归档，传递原始文件名
                    success, reason, archived_path = import_single_file(
                        tmp_file_path, 
                        archive=True, 
                        original_filename=uploaded_file.name
                    )
                    
                    # 删除临时文件
                    try:
                        os.unlink(tmp_file_path)
                    except:
                        pass
                    
                    if success:
                        imported += 1
                    else:
                        failed.append(f"{uploaded_file.name}: {reason}")
                
                if imported > 0:
                    st.success(f"成功导入 {imported} 篇作文！")
                if failed:
                    st.warning("部分文件导入失败：")
                    for fail in failed:
                        st.write(f"- {fail}")
                st.rerun()
    
    with col2:
        st.write(f"📂 扫描作文目录（当前目录：{COMPOSITION_DIR}）")
        if st.button("🔍 扫描新增作文", type="primary"):
            with st.spinner("正在扫描..."):
                result = scan_composition_dir(rescan=False)
            st.success(f"扫描完成！新增导入 {result['imported']} 篇作文，跳过 {result['skipped']} 篇")
            if result['failed']:
                st.warning("部分文件导入失败：")
                for fail in result['failed']:
                    st.write(f"- {fail['file']}: {fail['reason']}")
            st.rerun()
        
        if st.button("🔄 重新扫描全部作文（重新分析分类标签）"):
            with st.spinner("正在重新扫描..."):
                result = scan_composition_dir(rescan=True)
            msg = f"重新扫描完成！"
            if result.get('deleted', 0) > 0:
                msg += f" 删除了 {result['deleted']} 条不存在的记录"
            msg += f" 更新了 {result['imported']} 篇作文"
            st.success(msg)
            if result['failed']:
                st.warning("部分文件导入失败：")
                for fail in result['failed']:
                    st.write(f"- {fail['file']}: {fail['reason']}")
            st.rerun()

with tab2:
    st.header("作文列表")
    
    compositions = search_compositions(
        keyword=keyword if keyword else None,
        category=category if category else None,
        tag=tag if tag else None
    )
    
    if compositions:
        # 多选导出功能
        st.subheader("选择作文导出")
        export_ids = []
        for comp in compositions:
            if st.checkbox(f"📄 {comp['title']} ({comp['category']})", key=f"export_{comp['id']}"):
                export_ids.append(comp['id'])
        
        if export_ids:
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("📥 导出选中作文（单个文件）", type="primary"):
                    # 合并成一个文件
                    combined_content = ""
                    for comp_id in export_ids:
                        comp = get_composition_by_id(comp_id)
                        if comp:
                            combined_content += f"{'='*50}\n"
                            combined_content += f"标题：{comp['title']}\n"
                            combined_content += f"分类：{comp['category']}\n"
                            combined_content += f"标签：{', '.join(comp['tags'])}\n"
                            combined_content += f"{'='*50}\n\n"
                            combined_content += f"{comp['content']}\n\n"
                    st.download_button(
                        "📥 下载合并后的作文文件",
                        data=combined_content,
                        file_name=f"精选作文_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain"
                    )
            with col2:
                st.info("💡 提示：单篇导出可以在「作文详情」页操作")
        
        st.divider()
        
        df_data = []
        for comp in compositions:
            df_data.append({
                "ID": comp['id'],
                "标题": comp['title'],
                "分类": comp['category'],
                "标签": ", ".join(comp['tags']),
                "字数": comp['word_count'],
                "导入时间": comp['created_at'][:10]
            })
        df = pd.DataFrame(df_data)
        st.dataframe(df, width="stretch", hide_index=True)
        
        st.subheader("作文卡片")
        for comp in compositions:
            with st.expander(f"📄 {comp['title']} ({comp['category']})"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**标签**：{', '.join(comp['tags'])}")
                    st.write(f"**字数**：{comp['word_count']}")
                    st.write(f"**摘要**：{comp['summary']}")
                with col2:
                    delete_key = f"delete_{comp['id']}"
                    if st.button("🗑️ 删除", key=delete_key):
                        st.session_state[f"confirm_delete_{comp['id']}"] = True
                
                # 显示确认对话框
                if st.session_state.get(f"confirm_delete_{comp['id']}", False):
                    st.warning(f"确定要删除《{comp['title']}》吗？")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ 确认删除", key=f"confirm_{comp['id']}"):
                            success, file_path = delete_composition(comp['id'])
                            if success:
                                # 删除文件
                                if file_path and os.path.exists(file_path):
                                    try:
                                        os.remove(file_path)
                                    except:
                                        pass
                                st.success(f"成功删除《{comp['title']}》！")
                                st.session_state.pop(f"confirm_delete_{comp['id']}", None)
                                st.rerun()
                    with col_b:
                        if st.button("❌ 取消", key=f"cancel_{comp['id']}"):
                            st.session_state.pop(f"confirm_delete_{comp['id']}", None)
                            st.rerun()
    else:
        st.info("没有找到符合条件的作文")

with tab3:
    st.header("作文详情")
    
    compositions = search_compositions()
    if not compositions:
        st.info("还没有导入作文")
    else:
        comp_titles = [f"{comp['id']} - {comp['title']}" for comp in compositions]
        selected = st.selectbox("选择一篇作文查看详情", comp_titles)
        
        if selected:
            comp_id = int(selected.split(" - ")[0])
            comp = get_composition_by_id(comp_id)
            
            if comp:
                # 编辑模式状态
                edit_mode_key = f"edit_mode_{comp['id']}"
                is_editing = st.session_state.get(edit_mode_key, False)
                
                if is_editing:
                    # 编辑模式
                    st.subheader("✏️ 编辑作文")
                    
                    new_title = st.text_input("标题", value=comp['title'])
                    new_content = st.text_area("作文正文", value=comp['content'], height=400)
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("💾 保存修改", type="primary"):
                            # 重新分析
                            analysis = analyze_composition(new_content)
                            word_count = analysis['word_count']
                            
                            # 更新数据
                            update_data = {
                                'title': new_title,
                                'content': new_content,
                                'category': comp['category'],  # 保持原分类
                                'tags': comp['tags'],          # 保持原标签
                                'word_count': word_count,
                                'summary': analysis['summary']
                            }
                            
                            update_composition(comp['id'], update_data)
                            
                            # 同时更新文件
                            if comp['file_path'] and os.path.exists(comp['file_path']):
                                try:
                                    with open(comp['file_path'], 'w', encoding='utf-8') as f:
                                        f.write(new_content)
                                except Exception as e:
                                    st.warning(f"文件更新失败：{e}")
                            
                            st.success("✅ 保存成功！")
                            st.session_state[edit_mode_key] = False
                            st.rerun()
                    with col2:
                        if st.button("❌ 取消编辑"):
                            st.session_state[edit_mode_key] = False
                            st.rerun()
                else:
                    # 查看模式
                    st.subheader(comp['title'])
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**分类**：{comp['category']}")
                    with col2:
                        st.write(f"**字数**：{comp['word_count']}")
                    with col3:
                        st.write(f"**导入时间**：{comp['created_at'][:10]}")
                    
                    st.write(f"**标签**：{', '.join(comp['tags'])}")
                    st.write(f"**摘要**：{comp['summary']}")
                    
                    st.divider()
                    st.subheader("作文正文")
                    st.text_area(" ", comp['content'], height=400, label_visibility="collapsed")
                    
                    st.divider()
                    
                    # AI 分析结果区域
                    st.subheader("🤖 AI 分析")
                    
                    ai_result_key = f"ai_result_{comp['id']}"
                    # 显示已收藏的优秀句段
                    st.subheader("📚 已收藏的句段")
                    existing_favorites = get_favorite_sentences_by_composition_id(comp['id'])
                    if existing_favorites:
                        for fav in existing_favorites:
                            col1, col2 = st.columns([6, 1])
                            with col1:
                                st.markdown(f"> {fav['sentence']}")
                                if fav.get('reason'):
                                    st.caption(f"收藏理由: {fav['reason']}")
                            with col2:
                                delete_fav_key = f"delete_existing_fav_{fav['id']}"
                                if st.button("🗑️", key=delete_fav_key):
                                    st.session_state[f"confirm_del_existing_{fav['id']}"] = True
                            
                            if st.session_state.get(f"confirm_del_existing_{fav['id']}", False):
                                st.warning("确定要删除吗？")
                                a_col1, a_col2 = st.columns(2)
                                with a_col1:
                                    if st.button("✅ 确认", key=f"ok_del_{fav['id']}"):
                                        delete_favorite_sentence(fav['id'])
                                        st.session_state.pop(f"confirm_del_existing_{fav['id']}", None)
                                        st.rerun()
                                with a_col2:
                                    if st.button("❌ 取消", key=f"no_del_{fav['id']}"):
                                        st.session_state.pop(f"confirm_del_existing_{fav['id']}", None)
                                        st.rerun()
                            st.divider()
                    
                    if ai_result_key in st.session_state:
                        # 显示已保存的分析结果
                        ai_result = st.session_state[ai_result_key]
                        if ai_result.get('success'):
                            data = ai_result.get('data', {})
                            if 'strengths' in data:
                                st.markdown("### ✨ 作文优点")
                                for s in data['strengths']:
                                    st.markdown(f"- {s}")
                            if 'weaknesses' in data:
                                st.markdown("### 💭 可以改进的地方")
                                for w in data['weaknesses']:
                                    st.markdown(f"- {w}")
                            if 'suggestions' in data:
                                st.markdown("### 💡 改进建议")
                                for s in data['suggestions']:
                                    st.markdown(f"- {s}")
                            if 'highlight_sentences' in data:
                                st.markdown("### 🌟 优秀句子（可收藏）")
                                for idx, h in enumerate(data['highlight_sentences']):
                                    col1, col2 = st.columns([6, 1])
                                    with col1:
                                        st.markdown(f"> {h}")
                                    with col2:
                                        collect_key = f"collect_{comp['id']}_{idx}"
                                        if st.button("⭐ 收藏", key=collect_key):
                                            st.session_state[f"show_collect_form_{comp['id']}_{idx}"] = True
                                    
                                    if st.session_state.get(f"show_collect_form_{comp['id']}_{idx}", False):
                                        with st.form(key=f"form_collect_{comp['id']}_{idx}"):
                                            reason = st.text_input("收藏理由", value="AI 推荐的优秀句子")
                                            category = st.text_input("分类", value=comp['category'] or "其他")
                                            tags = st.text_input("标签（用逗号分隔）", value=",".join(comp['tags']))
                                            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                                            
                                            col_a, col_b = st.columns(2)
                                            with col_a:
                                                submit = st.form_submit_button("💾 保存", type="primary")
                                            with col_b:
                                                cancel = st.form_submit_button("❌ 取消")
                                            
                                            if submit:
                                                add_favorite_sentence(comp['id'], {
                                                    'sentence': h,
                                                    'source_text': comp['content'],
                                                    'reason': reason,
                                                    'category': category,
                                                    'tags': tag_list
                                                })
                                                st.success("✅ 收藏成功！")
                                                st.session_state.pop(f"show_collect_form_{comp['id']}_{idx}", None)
                                                st.rerun()
                                            if cancel:
                                                st.session_state.pop(f"show_collect_form_{comp['id']}_{idx}", None)
                                                st.rerun()
                                    st.divider()
                        else:
                            st.warning(f"分析失败：{ai_result.get('reason')}")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        if st.button("✏️ 编辑作文"):
                            st.session_state[edit_mode_key] = True
                            st.rerun()
                    with col2:
                        # 导出单个作文
                        st.download_button(
                            "📥 导出作文",
                            data=comp['content'],
                            file_name=comp['file_name'],
                            mime="text/plain"
                        )
                    with col3:
                        if st.button("🤖 AI 分析作文"):
                            # 检查是否可用
                            available, error = llm_module.check_llm_available()
                            if not available:
                                st.error(f"❌ OpenAI 库不可用: {error}")
                            else:
                                config = llm_module.load_config()
                                if not config.get("api_key"):
                                    st.warning("⚠️ 请先在「设置」页面配置 API Key")
                                else:
                                    with st.spinner("正在分析..."):
                                        result = llm_module.ai_analyze_composition(comp['content'])
                                        st.session_state[ai_result_key] = result
                                    if result.get('success'):
                                        st.success("分析完成！")
                                    else:
                                        st.error(f"分析失败：{result.get('reason')}")
                                    st.rerun()
                    with col4:
                        if st.button("✨ 手动收藏句段"):
                            st.session_state[f"show_manual_collect_{comp['id']}"] = True
                    
                    if st.session_state.get(f"show_manual_collect_{comp['id']}", False):
                        with st.form(key=f"form_manual_{comp['id']}"):
                            sentence = st.text_area("选择/输入你喜欢的句子", height=100)
                            reason = st.text_input("收藏理由")
                            category = st.text_input("分类", value=comp['category'] or "其他")
                            tags = st.text_input("标签（用逗号分隔）", value=",".join(comp['tags']))
                            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                submit = st.form_submit_button("💾 保存收藏", type="primary")
                            with col_b:
                                cancel = st.form_submit_button("❌ 取消")
                            
                            if submit and sentence:
                                add_favorite_sentence(comp['id'], {
                                    'sentence': sentence,
                                    'source_text': comp['content'],
                                    'reason': reason,
                                    'category': category,
                                    'tags': tag_list
                                })
                                st.success("✅ 收藏成功！")
                                st.session_state.pop(f"show_manual_collect_{comp['id']}", None)
                                st.rerun()
                            if cancel:
                                st.session_state.pop(f"show_manual_collect_{comp['id']}", None)
                                st.rerun()

with tab4:
    st.header("🌟 优秀句段收藏")
    
    stats = get_favorite_sentence_stats()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("收藏句段总数", stats['total'])
    with col2:
        st.info(f"分类统计: {stats['category_stats']}")
    
    favorites = get_favorite_sentences(category=fav_category if fav_category else None, tag=fav_tag if fav_tag else None)
    
    if favorites:
        for fav in favorites:
            with st.container():
                col1, col2 = st.columns([6, 1])
                with col1:
                    st.markdown(f"### 💬 {fav['sentence']}")
                    if fav.get('composition_title'):
                        st.caption(f"来源: 《{fav['composition_title']}》")
                    if fav.get('reason'):
                        st.write(f"**收藏理由**: {fav['reason']}")
                    if fav.get('category'):
                        st.write(f"**分类**: {fav['category']}")
                    if fav.get('tags'):
                        st.write(f"**标签**: {', '.join(fav['tags'])}")
                with col2:
                    delete_key = f"delete_fav_{fav['id']}"
                    if st.button("🗑️", key=delete_key):
                        st.session_state[f"confirm_delete_fav_{fav['id']}"] = True
                
                if st.session_state.get(f"confirm_delete_fav_{fav['id']}", False):
                    st.warning("确定要删除这条收藏吗？")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ 确认删除", key=f"confirm_del_fav_{fav['id']}"):
                            delete_favorite_sentence(fav['id'])
                            st.session_state.pop(f"confirm_delete_fav_{fav['id']}", None)
                            st.rerun()
                    with col_b:
                        if st.button("❌ 取消", key=f"cancel_del_fav_{fav['id']}"):
                            st.session_state.pop(f"confirm_delete_fav_{fav['id']}", None)
                            st.rerun()
                st.divider()
        
        # 导出所有收藏
        if st.button("📥 导出所有收藏", type="primary"):
            export_text = ""
            for idx, fav in enumerate(favorites, 1):
                export_text += f"【{idx}】\n"
                export_text += f"句段: {fav['sentence']}\n"
                if fav.get('composition_title'):
                    export_text += f"来源: {fav['composition_title']}\n"
                if fav.get('reason'):
                    export_text += f"理由: {fav['reason']}\n"
                if fav.get('category'):
                    export_text += f"分类: {fav['category']}\n"
                if fav.get('tags'):
                    export_text += f"标签: {', '.join(fav['tags'])}\n"
                export_text += "-" * 50 + "\n\n"
            
            st.download_button(
                "📥 下载文件",
                data=export_text,
                file_name=f"优秀句段收藏_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
    else:
        st.info("还没有收藏的优秀句段，先去作文详情页发现好句子吧！")

with tab5:
    st.header("⚙️ 设置")
    
    st.subheader("🤖 API Key 配置")
    
    config = llm_module.load_config()
    
    st.info("💡 提示：可以使用 DeepSeek API（推荐，性价比高），注册地址：https://platform.deepseek.com/")
    
    api_key = st.text_input(
        "API Key", 
        value=config.get("api_key", ""), 
        type="password"
    )
    base_url = st.text_input(
        "API Base URL", 
        value=config.get("base_url", "https://api.deepseek.com/v1")
    )
    model = st.text_input(
        "Model", 
        value=config.get("model", "deepseek-chat")
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("💾 保存配置", type="primary"):
            new_config = {
                "api_key": api_key,
                "base_url": base_url,
                "model": model
            }
            llm_module.save_config(new_config)
            st.success("✅ 配置已保存！")
    with col2:
        if st.button("📋 测试连接"):
            if not api_key:
                st.warning("请先输入 API Key 并保存")
            else:
                with st.spinner("测试连接..."):
                    success, message = llm_module.test_connection()
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    st.divider()
    st.subheader("📖 使用说明")
    st.markdown("""
1. **注册 DeepSeek**：访问 https://platform.deepseek.com/ 注册账号
2. **获取 API Key**：在控制台创建 API Key
3. **填入配置**：在上面输入框填入 API Key 并保存
4. **开始使用**：在作文详情页点击「AI 分析作文」
    """)
    
    status_col1, status_col2 = st.columns(2)
    with status_col1:
        available, error = llm_module.check_llm_available()
        if available:
            st.success("✅ OpenAI 库已安装")
            try:
                import openai
                st.info(f"版本: {getattr(openai, '__version__', '未知')}")
            except:
                pass
        else:
            st.error(f"❌ 需要安装：pip install openai (错误: {error})")
    with status_col2:
        if config.get("api_key"):
            st.success("✅ API Key 已配置")
        else:
            st.warning("⚠️ 未配置 API Key")
    
    st.divider()
    st.subheader("🔍 环境诊断")
    if st.button("运行诊断检查"):
        with st.spinner("检查中..."):
            try:
                import sys
                st.info(f"Python 路径: {sys.executable}")
                
                try:
                    import openai
                    st.success(f"✅ OpenAI 库已加载，版本: {getattr(openai, '__version__', '未知')}")
                except Exception as e:
                    st.error(f"❌ 导入 OpenAI 失败: {e}")
                    st.info("尝试运行: pip install openai --upgrade")
                
                st.divider()
                st.info("当前已安装的包:")
                try:
                    import pkg_resources
                    packages = [d for d in pkg_resources.working_set]
                    openai_pkg = [p for p in packages if p.key == 'openai']
                    if openai_pkg:
                        st.success(f"openai 版本: {openai_pkg[0].version}")
                except Exception as e:
                    pass
            except Exception as e:
                st.error(f"诊断失败: {e}")

