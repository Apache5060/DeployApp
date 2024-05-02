import streamlit as st

class MultiApp:
    def __init__(self):
        self.apps = []

    def add_app(self, title, func):
        """Add a new application page."""
        self.apps.append({
            "title": title,
            "function": func
        })

    def run(self):
        """Run the multi-app Streamlit application."""
        st.sidebar.title("Navigation")
        app = st.sidebar.radio(
            '',
            self.apps,
            format_func=lambda app: app['title'])
        app['function']()
