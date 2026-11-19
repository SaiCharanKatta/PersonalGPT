
import streamlit as st
import database
import html
import re
import sqlite3


def render_homepage():

    public = database.get_public_profile()
    if public:
        from admin_ai import connection

        conn = connection()
        try:
            row = conn.execute(
                "SELECT setting_value FROM site_settings WHERE setting_key = ?",
                ("accent_color",),
            ).fetchone()
        except sqlite3.OperationalError as exc:
            if "no such table: site_settings" not in str(exc):
                raise
            row = None
        finally:
            conn.close()
        color = row[0] if row else ""
        if isinstance(color, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            st.markdown(
                '<style>.eyebrow, [data-testid="stMetricValue"] { color: '
                + color + ' !important; }</style>',
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div class="eyebrow">PERSONAL GPT</div>',
        unsafe_allow_html=True
    )

    if not public:
        st.markdown("""
        <div class="hero-panel">
            <div class="eyebrow">WELCOME</div>
            <h1 style="font-size:42px; margin-top:15px;">
                Professional portfolio
            </h1>
            <p style="color:#A1A1AA; font-size:16px;">
                This portfolio is being prepared.
                Approved professional information will appear here soon.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.caption("Portfolio publication is pending approval.")
        return

    name = html.escape(str(public.get("full_name") or "Professional"))
    title = html.escape(str(public.get("professional_title") or ""))
    summary = public.get("professional_summary") or ""
    location = public.get("location") or ""

    skills = public.get("skills", [])
    projects = public.get("projects", [])
    education = public.get("education", [])
    experience = public.get("experience", [])
    certifications = public.get("certifications", [])
    languages = public.get("languages", [])

    # HERO: use native Streamlit layout instead of detached HTML blocks.
    st.markdown(
        '<div class="eyebrow">HELLO, WELCOME TO MY PORTFOLIO</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <h1 style="
            font-size:clamp(38px, 6vw, 64px);
            font-weight:800;
            line-height:1.1;
            margin-top:18px;
            margin-bottom:14px;
        ">{name}</h1>
        """,
        unsafe_allow_html=True
    )

    if title:
        st.subheader(title)

    if summary:
        st.write(summary)

    if location:
        st.caption("📍 " + str(location))

    # Compact professional metrics without an empty side panel.
    metric_columns = st.columns(4)

    metrics = [
        ("Projects", len(projects)),
        ("Skills", len(skills)),
        ("Experience", len(experience)),
        ("Education", len(education))
    ]

    for column, (label, value) in zip(metric_columns, metrics):
        with column:
            st.metric(label, value)

    st.divider()

    tabs = st.tabs([
        "Overview",
        "Skills",
        "Projects",
        "Experience",
        "Education",
        "Contact"
    ])

    # OVERVIEW
    with tabs[0]:

        st.header("About me")

        st.write(
            "I am a Computer Science graduate with a professional "
            "journey across customer communication, technical support "
            "and Level 2 troubleshooting. I enjoy investigating "
            "technology problems, learning new platforms and applying "
            "my technical knowledge to practical situations. My "
            "interests also include software development, databases "
            "and Artificial Intelligence."
        )

        if location:
            st.caption("Based in " + str(location))

        st.subheader("What I bring")

        a, b, c = st.columns(3)

        with a:
            st.markdown("""
            <div class="portfolio-card">
                <h3>Technology</h3>
                <p class="muted-text">
                    Technical foundations and continuous learning.
                </p>
            </div>
            """, unsafe_allow_html=True)

        with b:
            st.markdown("""
            <div class="portfolio-card">
                <h3>Problem solving</h3>
                <p class="muted-text">
                    Analytical thinking and practical projects.
                </p>
            </div>
            """, unsafe_allow_html=True)

        with c:
            st.markdown("""
            <div class="portfolio-card">
                <h3>Growth</h3>
                <p class="muted-text">
                    Adaptability and professional development.
                </p>
            </div>
            """, unsafe_allow_html=True)

        if languages:
            st.subheader("Languages")
            st.write(", ".join(
                str(item.get("language_name", ""))
                + (
                    " (" + str(item.get("proficiency")) + ")"
                    if item.get("proficiency") else ""
                )
                for item in languages
            ))

    # SKILLS
    with tabs[1]:

        st.header("Skills and technologies")

        if skills:

            categories = sorted({
                str(skill.get("category") or "Other").strip()
                for skill in skills
            })

            category_options = ["All categories"] + categories

            selected_category = st.selectbox(
                "Filter skills by category",
                category_options,
                key="portfolio_skill_category_filter"
            )

            filtered_skills = [
                skill for skill in skills
                if selected_category == "All categories"
                or str(skill.get("category") or "Other").strip()
                    == selected_category
            ]

            if selected_category == "All categories":

                grouped = {}

                for skill in filtered_skills:
                    category = str(
                        skill.get("category") or "Other"
                    ).strip()
                    grouped.setdefault(category, []).append(skill)

                for category in categories:
                    st.subheader(category)

                    columns = st.columns(3)

                    for index, skill in enumerate(grouped.get(category, [])):
                        skill_name = html.escape(
                            str(skill.get("skill_name") or "Skill")
                        )

                        with columns[index % 3]:
                            st.markdown(
                                f"""
                                <div class="portfolio-card">
                                    <span style="color:#D1D5DB;">✦</span>
                                    {skill_name}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

            else:

                columns = st.columns(3)

                for index, skill in enumerate(filtered_skills):
                    skill_name = html.escape(
                        str(skill.get("skill_name") or "Skill")
                    )

                    with columns[index % 3]:
                        st.markdown(
                            f"""
                            <div class="portfolio-card">
                                <span style="color:#D1D5DB;">✦</span>
                                {skill_name}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

        else:
            st.info("Skills will appear here.")

    # PROJECTS
    with tabs[2]:

        st.header("Selected projects")

        if projects:

            columns = st.columns(2)

            for index, project in enumerate(projects):

                with columns[index % 2]:

                    with st.container(border=True):

                        st.subheader(
                            project.get("project_name", "Project")
                        )

                        st.write(project.get("description", ""))

                        if project.get("technologies"):
                            st.caption(project["technologies"])

        else:
            st.info("Projects will appear here.")

    # EXPERIENCE
    with tabs[3]:

        st.header("Career journey")

        if experience:

            for job in experience:

                with st.container(border=True):

                    st.subheader(job.get("job_title", "Role"))
                    st.write(job.get("company", ""))

                    period = " – ".join(
                        str(value)
                        for value in [
                            job.get("start_date"),
                            "Present" if job.get("is_current")
                            else job.get("end_date")
                        ]
                        if value
                    )

                    if period:
                        st.caption(period)

                    st.write(job.get("description", ""))

        else:
            st.info("Experience details will appear here.")

    # EDUCATION
    with tabs[4]:

        st.header("Education")

        if education:

            for item in education:

                with st.container(border=True):

                    st.subheader(
                        item.get("qualification", "Education")
                    )

                    st.write(item.get("specialization", ""))
                    st.caption(item.get("institution", ""))

                    years = " – ".join(
                        str(value)
                        for value in [
                            item.get("start_year"),
                            item.get("end_year")
                        ]
                        if value
                    )

                    if years:
                        st.caption(years)

        else:
            st.info("Education details will appear here.")

        if certifications:

            st.subheader("Certifications")

            for cert in certifications:
                st.write(
                    str(cert.get("certification_name", ""))
                    + " — "
                    + str(cert.get("issuing_organization") or "")
                )

    # CONTACT
    with tabs[5]:

        st.header("Let's connect")
        st.write("Send a message using the contact form.")

        with st.form("portfolio_contact"):

            visitor_name = st.text_input("Your name")
            visitor_email = st.text_input("Your email")
            subject = st.text_input("Subject")
            message = st.text_area("Your message")

            submitted = st.form_submit_button("Send message")

            if submitted:

                try:

                    database.save_contact_message(
                        visitor_name,
                        visitor_email,
                        message,
                        subject=subject
                    )

                    st.success(
                        "Thank you! Your message has been received."
                    )

                except ValueError as error:
                    st.error(str(error))

                except Exception:
                    st.error(
                        "We could not submit your message. "
                        "Please try again."
                    )

    st.divider()
    st.caption("© " + name + " | Personal GPT")


# ================================================================
# PERSONAL_GPT_DYNAMIC_PUBLIC_RENDERER
# Renders additional approved portfolio content.
# Existing homepage, tabs and contact form remain intact.
# ================================================================

import streamlit as _pg_streamlit
import database as _pg_database


_pg_original_render_homepage = render_homepage


def _pg_render_approved_extensions():
    data = _pg_database.get_public_profile()

    intro_items = data.get("portfolio_intro", [])
    highlights = data.get("portfolio_highlights", [])
    custom_fields = data.get("custom_fields", [])

    if not intro_items and not highlights and not custom_fields:
        return

    _pg_streamlit.divider()
    _pg_streamlit.header("Additional Portfolio Information")

    for item in intro_items:
        heading = item.get("heading") or "About Me"
        body = item.get("body") or ""

        if body.strip():
            with _pg_streamlit.container(border=True):
                _pg_streamlit.subheader(heading)
                _pg_streamlit.write(body)

    if highlights:
        _pg_streamlit.subheader("Highlights")

        columns = _pg_streamlit.columns(
            min(3, len(highlights))
        )

        for index, item in enumerate(highlights):
            with columns[index % len(columns)]:
                with _pg_streamlit.container(border=True):
                    icon = item.get("icon") or "✦"
                    _pg_streamlit.markdown(
                        f"### {icon} {item.get('title', '')}"
                    )
                    _pg_streamlit.write(
                        item.get("description", "")
                    )

    if custom_fields:
        _pg_streamlit.subheader("More About Me")

        columns = _pg_streamlit.columns(
            min(3, len(custom_fields))
        )

        for index, item in enumerate(custom_fields):
            with columns[index % len(columns)]:
                with _pg_streamlit.container(border=True):
                    _pg_streamlit.caption(
                        item.get("field_label", "")
                    )
                    _pg_streamlit.markdown(
                        f"**{item.get('field_value', '')}**"
                    )


def render_homepage():
    _pg_original_render_homepage()
    _pg_render_approved_extensions()
