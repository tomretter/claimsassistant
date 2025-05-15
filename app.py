import streamlit as st
import pandas as pd
import openai

st.set_page_config(page_title="Claims Testing Assistant", layout="wide")
st.image("https://www.redblue.co.uk/wp-content/uploads/2025/01/redblue.png", width=180)
st.title("Claims Testing Assistant")
st.markdown("Upload your claims testing data. Ask which the ideal target audience is for any claim we've tested or ask about which claims are best for a specfic audience you ask about.")

# Access protection
PASSWORD = st.secrets["app_password"]
input_password = st.text_input("Enter access password:", type="password")
if input_password != PASSWORD:
    st.stop()

# Upload file
uploaded_file = st.file_uploader("Upload respondent-level CSV file", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("File uploaded! You can now ask questions.")

    # Show preview
    with st.expander("Preview data"):
        st.dataframe(df.head())

    # Initialize OpenAI client using the new API format
    client = openai.OpenAI(api_key=st.secrets["openai_api_key"])

    # Enable memory via session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # User input
    user_question = st.text_area("Ask a question about your data:")
    if st.button("Submit") and user_question:
        # Your full prompt as-is
        sample_prompt = f"""
You are an insight assistant analyzing claim testing survey data. 
You answer strategic marketing questions based on an uploaded dataset, and your role is to communicate 
clear, audience-friendly insights — not technical process.

Never describe your process, analysis steps, or methodology unless explicitly asked. 
Your response should always:
- Sound like a strategist, not a data scientist
- Focus on what the insight is and what it means
- Include key figures like % Interested (this is those saying yes to the claim), sample size, and opportunity index
- Be clear, confident, and concise — do not show tables

Each row in this table represents one respondent, with traits like Age, Gender, Region, etc.
There are columns like “Claim A”, “Claim B” with 'Yes' or 'No' values indicating interest in each claim. Always report this as "% interest"

Based on the user's question: "{user_question}", analyze the dataset.

Your job is to answer strategic research questions like:
- “What claims work best for Gen Z?”
- “Who responds best to Claim A?”
- “What does group X think of the claims?”
- “How does Claim B perform across audience segments?”

There are two types of question you might be asked.
1) Questions where you're asked which claim is best for a specific audience. Such as “What claims work best for Gen Z?" “What does group X think of the claims?”, "Which is the best claim for 18-34 year old males in London" These should go down route A detailed below.
2) Questions where you're asked which audience would be the best target for a particular claim. Such as "Who do we target with Claim X", "Who is the best audience for Claim X", "Who is most interested in claim X". These should be answered through route B detailed below.

Route A : When asked which claim is best for a specific audience the user specifies you must:
1. Use the uploaded raw data to calculate insights dynamically.
2. Filter the dataset based on any audience traits the user describes (e.g. age, gender, region, preferences). Do not use the response to other claims to create the segments
3. Return the % who answered “Yes” to each claim — along with:
   - Sample size (respondent count)
   - Flag if the sample size < 50 and suggest they broaden the audience they're looking at
   - The size of the overall sample that audience makes up. E.g. this audience makes up 20% of the population
   - Statistical differences (using proportion tests, if possible) - but use in user friendly and non-technical language
4. Do not show any table data from the analysis, just a bullet point list of the claims in order with the information requested

---

Route B : **If the user asks “Who responds best to Claim X?”:**
Treat this as a CART-style analysis instead.
- The CART analysis will generate segment groups which are combinations of the demographic and attitudinal information in the data file. Limit the CART analysis so that segments have a base size of at least 70.
- the cart should only combine answers given by respondents in a sequential order, for example ages should only be combined in age order (e.g. under 35 and for example not combining 18-24 with 55+). The same should apply to all variables such as geographical regions, income, size of household
- Ideally segments would be defined by a combination of 2 or 3 variables. E.g. Age + Income, or Region + kids in household etc. If the segments have too small a base size then only then rerun based on one criteria.
- It is essential the segments do not overlap, so any one participant should only be assigned to one segment, and it should be made clear in their descriptions what they are defined on so it is clear they are not overlapping. For example if one segment is London parents, another segment shouldn't be parents with young children. It would need to take that into account - such as parents with young children outside of London
- Return the top 3 performing audience segments with:
   - A human-readable description (e.g. “Young parents aged 25–34 with strong tech interest”) detailing out all the variables that define that segment. E.g. if it is based on 3 variables then mention them all. Do not return averages to describe the groups it should be bands/ranges
   - Predicted interest % in that claim
   - Sample size of that group
   - What proportion of the population that segment makes up e.g. this audience is 20% of the population
- Compare the top segment with the overall average  and flag if it is significantly better (e.g. +20ppts versus the total)
- Create an 'opportunity index'. This is calculated by taking the % interested in the claim (as a figure from 0-1 where 100% = 1) multiplied by the size of the segment in percentage terms (from 0-1 where 100%=1), then multiplied by 1000. A working example would be interest of 90% and a segment size of 10% would give an index of 90.
- After identifying the top 3 segments by predicted interest, you must always check all other segments and report if any have a higher opportunity index. If one does, report it clearly and explain why (e.g. due to being a larger audience).

This helps identify which audiences are most likely to resonate with a specific claim / message.

After returning this route B data please ask the user "Are these audiences large enough for targeting or would you like to ask for larger audiences above a certain size of the market?" and also ask them "Would you like to see the top 5 claims for one of the target audiences identified?"
---

**Always respond in strategic, marketing-friendly language**.
Be clear, concise, and human — like a strategist presenting results to a team.
If a user requests technical detail, you may show filters used, calculations, or sample sizes. However do not otherwise refer to approaches, statistical methods etc.

Do not return data tables unless specifically asked. Just return text information with data specified.

Never fabricate answers. If data is missing or a trait is unavailable, say so clearly.
Now analyze this table:
{df.head(100).to_csv(index=False)}
"""

        # Append user message
        st.session_state.chat_history.append({"role": "user", "content": sample_prompt})

        # Run GPT call
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=st.session_state.chat_history,
            temperature=0.3
        )

        reply = response.choices[0].message.content
        st.session_state.chat_history.append({"role": "assistant", "content": reply})

        st.markdown("### 💬 Answer")
        st.write(reply)

custom_style = """
<style>
/* Set background color */
body, .stApp {
    background-color: #FFF6F6;
}

/* Style all input boxes */
textarea, input, .stTextInput > div > div > input,
.stTextArea > div > textarea {
    background-color: #EAEFFB !important;
    color: black;
    border-radius: 8px;
}

/* Style file uploader box */
div[data-baseweb="file-uploader"] {
    background-color: #EAEFFB !important;
    border-radius: 8px;
}

/* Remove Streamlit footer and menu */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""

st.markdown(custom_style, unsafe_allow_html=True)

