import streamlit as st
import uuid
from datetime import datetime

# ─────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────
st.set_page_config(
    page_title="할 일 관리",
    page_icon="📋",
    layout="centered",
)

# ─────────────────────────────────────────
# 상수
# ─────────────────────────────────────────
CATEGORIES = {
    "work":      ("업무",  "#3B82F6"),
    "personal":  ("개인",  "#10B981"),
    "parenting": ("육아",  "#8B5CF6"),
}

# ─────────────────────────────────────────
# CSS 주입
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');

html, body, [class*="css"], .stMarkdown, .stTextInput, button {
    font-family: 'Noto Sans KR', sans-serif !important;
}

/* 전체 배경 */
.stApp { background: #F8F9FA; }

/* 메인 컨텐츠 최대 너비 */
.block-container {
    max-width: 700px !important;
    padding-top: 1.5rem !important;
}

/* 헤더 카드 */
.header-card {
    background: #fff;
    border-radius: 14px;
    padding: 20px 24px 18px;
    margin-bottom: 16px;
    box-shadow: 0 4px 16px rgba(0,0,0,.07);
}
.header-card h2 {
    font-size: 1.3rem;
    font-weight: 700;
    color: #111827;
    margin: 0 0 4px 0;
}
.progress-meta {
    font-size: 0.82rem;
    color: #6B7280;
    margin-bottom: 10px;
}

/* 입력 폼 카드 */
.form-card {
    background: #fff;
    border-radius: 14px;
    padding: 16px 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(0,0,0,.07);
}

/* 할 일 항목 래퍼 */
.todo-row {
    background: #fff;
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 8px;
    box-shadow: 0 1px 4px rgba(0,0,0,.07);
    display: flex;
    align-items: center;
    gap: 10px;
}

/* 뱃지 */
.badge {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 500;
    padding: 2px 9px;
    border-radius: 999px;
    white-space: nowrap;
    margin-top: 3px;
}

/* 완료 텍스트 */
.done-text {
    text-decoration: line-through;
    color: #9CA3AF !important;
}
.normal-text { color: #111827; }

/* 빈 상태 */
.empty-state {
    text-align: center;
    padding: 48px 16px;
    color: #6B7280;
    font-size: 0.97rem;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
}

/* 수정 모드 카드 */
.edit-card {
    background: #FFFBEB;
    border: 2px solid #FCD34D;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 8px;
}

/* Streamlit 컴포넌트 미세 조정 */
.stTextInput > div > div > input {
    border-radius: 8px !important;
    background: #F3F4F6 !important;
    font-family: 'Noto Sans KR', sans-serif !important;
}
.stSelectbox > div > div {
    border-radius: 8px !important;
    background: #F3F4F6 !important;
}
.stButton > button {
    border-radius: 8px !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    font-weight: 500 !important;
}
.stTabs [data-baseweb="tab-list"] {
    background: #fff;
    border-radius: 10px;
    padding: 4px;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
    margin-bottom: 16px;
    gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    font-weight: 500 !important;
}
/* 진행률 바 둥글게 */
.stProgress > div > div > div > div { border-radius: 999px !important; }

/* 불필요한 빈공간 제거 */
div[data-testid="column"] { gap: 0 !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# 세션 상태 초기화
# ─────────────────────────────────────────
if "todos" not in st.session_state:
    st.session_state.todos: list[dict] = []

if "editing_id" not in st.session_state:
    st.session_state.editing_id = None


# ─────────────────────────────────────────
# 헬퍼 함수
# ─────────────────────────────────────────
def now_iso() -> str:
    return datetime.now().isoformat()

def get_scoped(cat: str) -> list:
    if cat == "all":
        return st.session_state.todos
    return [t for t in st.session_state.todos if t["category"] == cat]

def badge_html(category: str) -> str:
    label, color = CATEGORIES.get(category, ("?", "#888"))
    bg = color + "22"
    return f'<span class="badge" style="background:{bg};color:{color};">{label}</span>'

def tab_label(cat: str) -> str:
    """탭 레이블: 카테고리명 (완료/전체)"""
    label = "전체" if cat == "all" else CATEGORIES[cat][0]
    items = get_scoped(cat)
    if not items:
        return label
    done = sum(1 for t in items if t["completed"])
    return f"{label} ({done}/{len(items)})"

def render_todo_list(cat: str):
    """필터링된 할 일 목록을 렌더링한다."""
    filtered = get_scoped(cat)

    # ── 빈 상태 ──
    if not filtered:
        if len(st.session_state.todos) > 0 and all(t["completed"] for t in get_scoped(cat)):
            msg = "🎉 모두 완료했습니다!"
        else:
            msg = "📋 할 일을 추가해보세요"
        st.markdown(f'<div class="empty-state">{msg}</div>', unsafe_allow_html=True)
        return

    # ── 항목 렌더링 ──
    for todo in filtered:
        is_editing = st.session_state.editing_id == todo["id"]
        _, color   = CATEGORIES.get(todo["category"], ("?", "#888"))

        if is_editing:
            # ── 수정 모드 ──
            st.markdown('<div class="edit-card">', unsafe_allow_html=True)
            cat_keys   = list(CATEGORIES.keys())
            cat_labels = [CATEGORIES[k][0] for k in cat_keys]

            ec1, ec2 = st.columns([5, 2])
            with ec1:
                edit_text = st.text_input(
                    "수정 내용",
                    value=todo["text"],
                    label_visibility="collapsed",
                    key=f"edit_text_{todo['id']}",
                )
            with ec2:
                cur_idx = cat_keys.index(todo["category"]) if todo["category"] in cat_keys else 0
                edit_cat_label = st.selectbox(
                    "카테고리",
                    cat_labels,
                    index=cur_idx,
                    label_visibility="collapsed",
                    key=f"edit_cat_{todo['id']}",
                )

            bs, bc = st.columns(2)
            with bs:
                if st.button("✅ 저장", key=f"save_{todo['id']}", use_container_width=True):
                    new_cat = cat_keys[cat_labels.index(edit_cat_label)]
                    if edit_text.strip():
                        for t in st.session_state.todos:
                            if t["id"] == todo["id"]:
                                t["text"]      = edit_text.strip()
                                t["category"]  = new_cat
                                t["updatedAt"] = now_iso()
                                break
                        st.session_state.editing_id = None
                        st.rerun()
                    else:
                        st.warning("내용을 입력해주세요.")
            with bc:
                if st.button("✖ 취소", key=f"cancel_{todo['id']}", use_container_width=True):
                    st.session_state.editing_id = None
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        else:
            # ── 일반 모드 ──
            text_cls = "done-text" if todo["completed"] else "normal-text"
            col_chk, col_txt, col_btn = st.columns([1, 8, 2])

            with col_chk:
                checked = st.checkbox(
                    "",
                    value=todo["completed"],
                    key=f"chk_{todo['id']}",
                    label_visibility="collapsed",
                )
                if checked != todo["completed"]:
                    for t in st.session_state.todos:
                        if t["id"] == todo["id"]:
                            t["completed"] = not t["completed"]
                            t["updatedAt"] = now_iso()
                            break
                    st.rerun()

            with col_txt:
                st.markdown(
                    f'<div style="padding-top:2px;">'
                    f'<span class="{text_cls}" style="font-size:0.97rem;">{todo["text"]}</span><br>'
                    f'{badge_html(todo["category"])}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            with col_btn:
                be, bd = st.columns(2)
                with be:
                    if st.button("✏️", key=f"edit_{todo['id']}", help="수정"):
                        st.session_state.editing_id = todo["id"]
                        st.rerun()
                with bd:
                    if st.button("🗑", key=f"del_{todo['id']}", help="삭제"):
                        st.session_state.todos = [
                            t for t in st.session_state.todos if t["id"] != todo["id"]
                        ]
                        if st.session_state.editing_id == todo["id"]:
                            st.session_state.editing_id = None
                        st.rerun()

    # ── 완료 항목 일괄 삭제 ──
    completed_in_view = [t for t in filtered if t["completed"]]
    if completed_in_view:
        st.divider()
        col_l, col_r = st.columns([3, 1])
        with col_r:
            if st.button(
                f"완료 {len(completed_in_view)}건 삭제",
                key=f"clear_done_{cat}",
                type="secondary",
                use_container_width=True,
            ):
                ids_to_remove = {t["id"] for t in completed_in_view}
                st.session_state.todos = [
                    t for t in st.session_state.todos if t["id"] not in ids_to_remove
                ]
                st.rerun()


# ─────────────────────────────────────────
# ① 헤더 — 진행률
# ─────────────────────────────────────────
all_todos = st.session_state.todos
total = len(all_todos)
done  = sum(1 for t in all_todos if t["completed"])
pct   = int(done / total * 100) if total > 0 else 0

st.markdown('<div class="header-card">', unsafe_allow_html=True)
st.markdown("## 📋 할 일 관리")

if total == 0:
    meta = "할 일이 없습니다"
elif done == total:
    meta = "모두 완료했습니다! 🎉"
else:
    meta = f"{done} / {total} 완료 ({pct}%)"

st.markdown(f'<p class="progress-meta">{meta}</p>', unsafe_allow_html=True)
st.progress(pct / 100)
st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────
# ② 입력 폼
# ─────────────────────────────────────────
st.markdown('<div class="form-card">', unsafe_allow_html=True)

cat_keys   = list(CATEGORIES.keys())                 # work, personal, parenting
cat_labels = [CATEGORIES[k][0] for k in cat_keys]   # 업무, 개인, 육아

fc1, fc2, fc3 = st.columns([5, 2, 1])
with fc1:
    new_text = st.text_input(
        "할 일",
        placeholder="할 일을 입력하세요",
        label_visibility="collapsed",
        key="new_todo_input",
    )
with fc2:
    selected_label = st.selectbox(
        "카테고리",
        cat_labels,
        label_visibility="collapsed",
        key="new_todo_cat",
    )
with fc3:
    add_clicked = st.button("＋", type="primary", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# 추가 처리
if add_clicked:
    if new_text.strip():
        selected_cat = cat_keys[cat_labels.index(selected_label)]
        st.session_state.todos.append({
            "id":        str(uuid.uuid4()),
            "text":      new_text.strip(),
            "category":  selected_cat,
            "completed": False,
            "createdAt": now_iso(),
            "updatedAt": now_iso(),
        })
        st.rerun()
    else:
        st.warning("⚠️ 할 일 내용을 입력해주세요.")


# ─────────────────────────────────────────
# ③ 카테고리 탭 + 할 일 목록
# ─────────────────────────────────────────
tab_keys   = ["all"] + cat_keys
tab_labels = [tab_label(k) for k in tab_keys]

tabs = st.tabs(tab_labels)

for tab_obj, cat_key in zip(tabs, tab_keys):
    with tab_obj:
        render_todo_list(cat_key)
