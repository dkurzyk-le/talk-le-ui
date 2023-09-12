import streamlit as st
from streamlit_option_menu import option_menu
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, ColumnsAutoSizeMode, JsCode
from streamlit_chat import message
import streamlit_authenticator as stauth
import requests
import pandas as pd
import json
import yaml
from yaml.loader import SafeLoader

URL_SEARCH = 'https://engine.talk.locationengine.ai/search'
URL_CHAT = 'https://engine.talk.locationengine.ai/talk'

#URL_SEARCH = 'http://localhost:8444/search'
#URL_CHAT = 'http://localhost:8444/talk'

headers = {'Accept': '*/*',
             'Accept-Encoding': 'gzip, deflate br',
             'Connection': 'keep-alive',
             'Content-Length': '192',
             'Content-Type': 'application/json',
          }

st.set_page_config(
    layout="wide",
    page_title="LE Talk",
    page_icon="👋"
)

## Hide default streamlit menu
hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

# Load authenticator config file
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)


boards = ['Semantic search', 'Chat with data']
default_index = 0

result = {"Product ID": [], "Title": [], "Text": [], "Score": []}

df = pd.DataFrame(result)

@st.cache_data
def search_request(text):
    query = json.dumps({
        "query": text,
        "top_n": 6,
        "vectordb": "qdrant"
    })

    r = requests.post(url=URL_SEARCH, data=query, headers=headers)

    response =  json.loads(r.text)

    product_id = []
    title = []
    content = []
    score = []
    for res in response:
        product_id.append(res['product_id'])
        title.append(res['title'])
        content.append(res['text'])
        score.append(res['score'])

    result = {"Product ID": product_id, "Title": title, "Text": content, "Score": score}

    df = pd.DataFrame(result)
    return df

# @st.cache_data
def talk_request(text):
    query = json.dumps({
        "query": text,
        "vectordb": "qdrant"
    })

    r = requests.post(url=URL_CHAT, data=query, headers=headers)

    req =  json.loads(r.text)

    return req

def semantic_search_board():
    global df
    _df = None

    st.title('Semantic search')

    text = st.text_input(label="Query")

    if st.button('Search'):
        df = search_request(text)

        st.table(df)

    # if _df is None:
    #     _df = df

    # print(df)

    # gb = GridOptionsBuilder.from_dataframe(_df)
    # # gb.configure_pagination(paginationAutoPageSize=True) #Add pagination
    # # gb.configure_side_bar() #Add a sidebar
    # # gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children") #Enable multi-row selection
    # gb.configure_selection('multiple', use_checkbox=False, groupSelectsChildren="Group checkbox select children")

    # gridOptions = gb.build()

    # custom_css = {
    #     ".ag-header-cell-label": {"justify-content": "center"},
    #     ".ag-header-group-cell-label": {"justify-content": "center"},
    #     ".ag-cell-focus": {"border-color": "red"},
    #     "--ag-range-selection-border-color": {"border-color": "red"},
    # }

    # grid_response = AgGrid(
    #     _df,
    #     gridOptions=gridOptions,
    #     data_return_mode='FILTERED', 
    #     update_mode='MODEL_CHANGED', 
    #     # theme='blue', #Add theme color to the table
    #     enable_enterprise_modules=False,
    #     fit_columns_on_grid_load=True,
    #     height=700, 
    #     width='100%',
    #     columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
    #     theme='material',
    #     reload_data=True,
    #     allow_unsafe_jscode = True,
    #     custom_css=custom_css
    # )

    # selected = grid_response['selected_rows'] 
    # if len(selected) > 0:
    #     print(selected)
    #     st.text(selected)



def get_text():
    input_text = st.text_input("You : ", "", key = "input")
    return input_text

def chat_with_data_board():
    if 'generated' not in st.session_state:
        st.session_state['generated'] = []
    if 'past' not in st.session_state:
        st.session_state['past'] = []

    user_input = get_text()

    if user_input:
        output = talk_request(user_input)

        # Store the output
        st.session_state.past.append(user_input)
        st.session_state.generated.append(output['response'])

        # with st.sidebar:
        #     st.write(output['sources'])

    # Finally we display the chat history

    if st.session_state['generated']:

        for i in range(len(st.session_state['generated']) -1, -1, -1):
            message(st.session_state["generated"][i], key=str(i))
            message(st.session_state["past"][i], is_user=True, key=str(i) + '_user')



def main():

    name, authentication_status, username = authenticator.login('Login', 'main')
    print(authentication_status)
    if authentication_status:
        col1, col2 = st.columns([8, 1], gap="small")
                    
        with col2:
            authenticator.logout('Logout', 'main')
        
            st.write(f'Welcome *{name}*')

            layout = True

        with st.sidebar:

            selected = option_menu("Main Menu", boards, 
            icons=[ 'search', 'megaphone'], menu_icon="app-indicator", default_index=default_index,
            styles={
                    # "container": {"padding": "5!important", "background-color": "#fafafa"},
                    "icon": {"color": "#00aeef", "font-size": "25px", "--hover-color":"white"}, 
                    # "nav": {"--hover-color":"navy"},
                    # "nav-item": {"--hover-color":"navy"},
                    "menu-title": {"color":"#00aeef"},
                    "menu-icon": {"color":"#00aeef"},
                    "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#b2e6fa"},
                    "nav-link-selected": {"background-color": "#f3f3f3", "color":"#00aeef"},
                }
            )

        if selected == boards[0]:
            semantic_search_board()
        else:
            chat_with_data_board()
    elif authentication_status == False:
        st.error('Username/password is incorrect')
    elif authentication_status == None:
        st.warning('Please enter your username and password')

if __name__ == "__main__":
    main()
