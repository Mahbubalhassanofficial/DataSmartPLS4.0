import streamlit as st

# You can tune these later if you want specific brand colors.
PRIMARY_COLOR = "#7b2cbf"   # DataSmartPLS purple
ACCENT_COLOR = "#4895ef"    # Accent blue


def render_app_header(page_title: str):
    """
    Standard header for all pages.
    `page_title` is the local page name, e.g. 'Home', 'Structural Model'.
    """
    col1, col2 = st.columns([2, 3])

    with col1:
        st.markdown(
            f"""
            <div style="font-size:1.4rem; font-weight:700; color:{PRIMARY_COLOR};">
                DataSmartPLS4.0
            </div>
            <div style="font-size:0.9rem; color:#666;">
                B’Deshi Emerging Research Lab · Synthetic PLS-SEM & SEM Data Studio
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div style="text-align:right; font-size:0.95rem; color:#555;">
                <span style="background-color:{ACCENT_COLOR}; color:white;
                             padding:3px 8px; border-radius:12px;">
                    {page_title}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")


def render_app_footer():
    """
    Standard footer for all pages.
    """
    st.markdown("---")
    st.markdown(
        """
        <div style="font-size:0.85rem; color:#777;">
            <b>DataSmartPLS4.0</b> · Designed for SmartPLS&nbsp;4, SEM, and fsQCA
            <br/>
            Built under the <b>B’Deshi Emerging Research Lab</b> – for teaching, simulation,
            and methodological research (not real-world inference).
        </div>
        """,
        unsafe_allow_html=True,
    )
