"""
auth.py — Lightweight password gate for the Acacus MNVR simulator.

The password is NEVER stored in code or in the repository. It is read from
Streamlit secrets:
  * Locally:  .streamlit/secrets.toml  (git-ignored)
  * On Cloud: the app's Settings → Secrets panel

If no password is configured at all, the app stays open (so local development
isn't blocked). To require a password, set APP_PASSWORD in secrets.
"""
from __future__ import annotations

import hmac

import streamlit as st


def _password_is_configured() -> bool:
    try:
        return bool(st.secrets.get("APP_PASSWORD", ""))
    except Exception:
        return False


def check_password() -> bool:
    """Return True if the user is authorised (or no password is configured).

    Renders a centred login form and halts the rest of the app until the
    correct password is entered. Uses a constant-time comparison.
    """
    # No password set anywhere → app is open (local dev convenience).
    if not _password_is_configured():
        return True

    if st.session_state.get("auth_ok"):
        return True

    # Login UI
    st.markdown(
        """
        <div style='max-width:420px;margin:8vh auto 0 auto;text-align:center'>
          <div style='font-size:2rem'>🛰️</div>
          <div style='font-size:1.4rem;font-weight:800;color:#1F3A5F;margin-top:4px'>
          Acacus MNVR Simulator</div>
          <div style='color:#8A94A6;font-size:0.9rem;margin-bottom:18px'>
          Relocation Feasibility Study — restricted access</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col = st.columns([1, 2, 1])[1]
    with col:
        pw = st.text_input("Password", type="password", key="pw_input",
                           placeholder="Enter access password")
        if st.button("Enter", use_container_width=True):
            actual = str(st.secrets.get("APP_PASSWORD", ""))
            if hmac.compare_digest(pw, actual):
                st.session_state.auth_ok = True
                st.session_state.pop("pw_input", None)
                st.rerun()
            else:
                st.error("Incorrect password.")
        st.caption("Access is limited to reviewers of the Acacus MNVR feasibility "
                   "study. Contact the study owner for the password.")
    return False
