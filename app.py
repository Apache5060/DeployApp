from multiapp import MultiApp
from pages import insight_generator, chatbot_page
from templates.css import get_css


# Create an instance of the MultiApp class
app = MultiApp()

# Add pages to your application
app.add_app("Insight Generator", insight_generator.app)
app.add_app("Chatbot", chatbot_page.app)

# Run the application
if __name__ == '__main__':
    app.run()
