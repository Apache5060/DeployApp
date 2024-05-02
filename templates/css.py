def get_css():
    return """
    <style>
    body {
        background-color: #f4f4f9;
        color: #333; /* Ensuring general text color is black for readability */
    }
    .stTextArea, .stTextInput {
        background-color: #ffffff;
        color: #333; /* Black text color */
        border: 1px solid #ccc; /* Adding a subtle border */
    }
    .stButton>button {
        background-color: #4CAF50; /* A pleasant green background */
        color: white; /* White text for the button */
        border: none;
        padding: 10px 24px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px; /* Rounded corners for the button */
        transition: background-color 0.3s ease; /* Smooth transition for hover effect */
    }
    .stButton>button:hover {
        background-color: #45a049; /* Darker shade of green when hovered */
    }
    </style>
    """

