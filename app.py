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
update_composition_category = db_module.update_composition_category
update_composition_score = db_module.update_composition_score
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
    
    # 所有已有的分类（含自动分类中的固定分类）
    ALL_PRESET_CATEGORIES = [
        "成长感悟类", "亲情类", "友情类", "校园生活类",
        "写人记事类", "自然风景类", "传统文化类",
        "读后感类", "议论文类", "想象作文类", "其他"
    ]
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.write("📤 从本地选择文件导入（自动归档）")
        uploaded_files = st.file_uploader(
            "选择作文文件",
            type=['txt', 'docx'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            # 存入 session_state 以便配置
            if "pending_uploads" not in st.session_state:
                st.session_state.pending_uploads = []
            
            # 将新上传的文件加入暂存区（去重）
            existing_names = {p["name"] for p in st.session_state.pending_uploads}
            for f in uploaded_files:
                if f.name not in existing_names:
                    # 读取内容做预览
                    try:
                        raw = f.read()
                        preview = raw.decode("utf-8")[:200]
                    except:
                        preview = "(无法预览)"
                    st.session_state.pending_uploads.append({
                        "name": f.name,
                        "raw": raw,
                        "preview": preview,
                        "category": "",
                        "score": 0
                    })
                    existing_names.add(f.name)
        
        # 显示待配置的导入列表
        if st.session_state.get("pending_uploads"):
            st.write("---")
            st.markdown("**以下文件等待导入，请设置分类和评分：**")
            
            all_existing_categories = set(get_categories()) | set(ALL_PRESET_CATEGORIES)
            
            all_ready = True
            for idx, pending in enumerate(st.session_state.pending_uploads):
                with st.expander(f"📄 {pending['name']}", expanded=True):
                    st.caption(f"预览: {pending['preview']}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        # 分类：下拉框 + 自定义输入
                        cat_options = sorted(all_existing_categories)
                        selected_cat = st.selectbox(
                            "分类",
                            [""] + cat_options + ["✏️ 自定义..."],
                            key=f"cat_select_{idx}"
                        )
                        if selected_cat == "✏️ 自定义...":
                            custom_cat = st.text_input("请输入自定义分类", key=f"cat_custom_{idx}")
                            final_cat = custom_cat.strip()
                        else:
                            final_cat = selected_cat
                        
                        st.session_state.pending_uploads[idx]["category"] = final_cat
                    
                    with c2:
                        # 评分：1-5 星
                        score = st.select_slider(
                            "评分",
                            options=[0, 1, 2, 3, 4, 5],
                            value=st.session_state.pending_uploads[idx]["score"],
                            format_func=lambda x: "未评分" if x == 0 else "⭐" * x,
                            key=f"score_slider_{idx}"
                        )
                        st.session_state.pending_uploads[idx]["score"] = score
                    
                    if not final_cat:
                        all_ready = False
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ 确认导入", type="primary", disabled=not all_ready):
                    imported = 0
                    failed = []
                    for pending in st.session_state.pending_uploads:
                        # 写入临时文件
                        ext = os.path.splitext(pending["name"])[1]
                        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                            tmp.write(pending["raw"])
                            tmp_path = tmp.name
                        
                        cat = pending["category"] if pending["category"] else None
                        score_val = pending["score"] if pending["score"] else 0
                        success, reason, _ = import_single_file(
                            tmp_path, archive=True,
                            original_filename=pending["name"],
                            category=cat,
                            score=score_val
                        )
                        try:
                            os.unlink(tmp_path)
                        except:
                            pass
                        
                        if success:
                            imported += 1
                        else:
                            failed.append(f"{pending['name']}: {reason}")
                    
                    st.session_state.pending_uploads = []
                    
                    if imported > 0:
                        st.success(f"成功导入 {imported} 篇作文！")
                    if failed:
                        st.warning("部分文件导入失败：")
                        for fail in failed:
                            st.write(f"- {fail}")
                    st.rerun()
            
            with col_b:
                if st.button("🗑️ 清空待导入列表"):
                    st.session_state.pending_uploads = []
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
            score_display = "⭐" * comp.get("score", 0) if comp.get("score", 0) > 0 else ""
            df_data.append({
                "ID": comp['id'],
                "标题": comp['title'],
                "分类": comp['category'],
                "评分": score_display,
                "标签": ", ".join(comp['tags']),
                "字数": comp['word_count'],
                "导入时间": comp['created_at'][:10]
            })
        df = pd.DataFrame(df_data)
        st.dataframe(df, width="stretch", hide_index=True)
        
        st.subheader("作文卡片")
        for comp in compositions:
            score_display = "⭐" * comp.get("score", 0) if comp.get("score", 0) > 0 else "未评分"
            with st.expander(f"📄 {comp['title']} ({comp['category']}) {score_display}"):
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
                
                # 修改分类 & 评分
                st.divider()
                st.markdown("**修改分类与评分：**")
                edit_c1, edit_c2, edit_c3 = st.columns([2, 2, 1])
                
                all_existing_categories = set(get_categories()) | set([
                    "成长感悟类", "亲情类", "友情类", "校园生活类",
                    "写人记事类", "自然风景类", "传统文化类",
                    "读后感类", "议论文类", "想象作文类", "其他"
                ])
                
                with edit_c1:
                    cat_options = sorted(all_existing_categories)
                    current_cat = comp['category'] or ""
                    new_cat = st.selectbox(
                        "分类",
                        [""] + cat_options + ["✏️ 自定义..."],
                        index=(cat_options.index(current_cat) + 1) if current_cat in cat_options else 0,
                        key=f"list_cat_{comp['id']}"
                    )
                    if new_cat == "✏️ 自定义...":
                        new_cat = st.text_input("输入自定义分类", value=current_cat, key=f"list_cat_custom_{comp['id']}")
                
                with edit_c2:
                    new_score = st.select_slider(
                        "评分",
                        options=[0, 1, 2, 3, 4, 5],
                        value=comp.get("score", 0),
                        format_func=lambda x: "未评分" if x == 0 else "⭐" * x,
                        key=f"list_score_{comp['id']}"
                    )
                
                with edit_c3:
                    st.write("")
                    st.write("")
                    if st.button("💾 保存", key=f"list_save_{comp['id']}"):
                        if new_cat and new_cat != "✏️ 自定义...":
                            update_composition_category(comp['id'], new_cat)
                        update_composition_score(comp['id'], new_score)
                        st.success("✅ 保存成功！")
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
                    
                    col_edit1, col_edit2 = st.columns(2)
                    with col_edit1:
                        new_category = st.text_input("分类", value=comp['category'])
                    with col_edit2:
                        new_score = st.select_slider(
                            "评分",
                            options=[0, 1, 2, 3, 4, 5],
                            value=comp.get("score", 0),
                            format_func=lambda x: "未评分" if x == 0 else "⭐" * x,
                            key=f"detail_edit_score_{comp['id']}"
                        )
                    
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
                                'category': new_category,
                                'tags': comp['tags'],
                                'word_count': word_count,
                                'summary': analysis['summary'],
                                'score': new_score
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
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.write(f"**分类**：{comp['category']}")
                    with col2:
                        st.write(f"**字数**：{comp['word_count']}")
                    with col3:
                        score_display = "⭐" * comp.get("score", 0) if comp.get("score", 0) > 0 else "未评分"
                        st.write(f"**评分**：{score_display}")
                    with col4:
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
                            if 'improvements' in data:
                                st.markdown("### 💭 改进建议")
                                for w in data['improvements']:
                                    st.markdown(f"- {w}")
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
                                        # 将分析结果格式化为文本
                                        analysis_text = llm_module.format_analysis_result(result.get('data', {}))
                                        
                                        # 如果已有分析内容，替换旧分析；否则追加
                                        if llm_module.has_analysis(comp['content']):
                                            # 找到旧分析的起始和结束位置
                                            marker = llm_module.ANALYSIS_MARKER_START.strip()
                                            marker_end = llm_module.ANALYSIS_MARKER_END.strip()
                                            start_idx = comp['content'].find(marker)
                                            end_idx = comp['content'].rfind(marker_end)
                                            if start_idx != -1 and end_idx != -1:
                                                end_idx += len(marker_end)
                                                base_content = comp['content'][:start_idx].rstrip()
                                            else:
                                                base_content = comp['content']
                                        else:
                                            base_content = comp['content']
                                        
                                        new_content = base_content + "\n\n" + analysis_text
                                        
                                        # 更新数据库中的内容
                                        update_data = {
                                            'title': comp['title'],
                                            'content': new_content,
                                            'category': comp['category'],
                                            'tags': comp['tags'],
                                            'word_count': comp['word_count'],
                                            'summary': comp['summary'],
                                            'score': comp.get('score', 0)
                                        }
                                        update_composition(comp['id'], update_data)
                                        
                                        # 同时更新本地文件
                                        if comp['file_path'] and os.path.exists(comp['file_path']):
                                            try:
                                                with open(comp['file_path'], 'w', encoding='utf-8') as f:
                                                    f.write(new_content)
                                            except Exception as e:
                                                st.warning(f"文件更新失败：{e}")
                                        
                                        st.success("✅ 分析完成！点评已附在作文末尾。")
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

