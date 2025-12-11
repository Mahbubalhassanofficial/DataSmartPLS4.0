import streamlit as st

# ---------------------------------------------------------
# BRAND COLORS (customizable)
# ---------------------------------------------------------
PRIMARY_COLOR = "#7b2cbf"   # DataSmartPLS core purple
ACCENT_COLOR = "#4895ef"    # Modern accent blue
TEXT_COLOR = "#444444"
SUBTEXT_COLOR = "#666666"


def render_app_header(page_title: str):
    """
    Standardized application header used across all pages.
    Includes tool name, lab name, and current page badge.
    """
    col1, col2 = st.columns([2.5, 1.5])

    with col1:
        st.markdown(
            f"""
            <div style="
                font-size:1.65rem; 
                font-weight:800; 
                color:{PRIMARY_COLOR};
                line-height:1.2;
            ">
                DataSmartPLS&nbsp;4.0
            </div>
            <div style="
                font-size:0.92rem; 
                color:{SUBTEXT_COLOR};
                margin-top:2px;
            ">
                B’Deshi Emerging Research Lab · Synthetic PLS-SEM & SEM Data Studio
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div style="
                text-align:right; 
                margin-top:8px;
            ">
                <span style="
                    background-color:{ACCENT_COLOR};
                    color:white;
                    padding:5px 12px;
                    border-radius:16px;
                    font-size:0.90rem;
                    font-weight:600;
                ">
                    {page_title}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='margin-top:0.6rem; margin-bottom:1.2rem;'>", unsafe_allow_html=True)


def render_app_footer():
    """
    Standardized footer displayed across all pages.
    Academic-style disclaimer and branding.
    """
    st.markdown("<hr style='margin-top:1.5rem; margin-bottom:0.8rem;'>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div style="
            font-size:0.85rem; 
            color:{SUBTEXT_COLOR};
            line-height:1.35;
            margin-bottom:0.9rem;
        ">
            <strong>DataSmartPLS&nbsp;4.0</strong> · A synthetic data simulation & diagnostics suite
            for <strong>SmartPLS 4</strong>, <strong>SEM</strong>, and <strong>fsQCA</strong>.
            <br/>
            Developed under the <strong>B’Deshi Emerging Research Lab</strong> — for educational use,
            methodological experimentation, and simulation-only research (not real-world inference).
        </div>
        """,
        unsafe_allow_html=True,
    )
