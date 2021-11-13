mkdir -p ~/.streamlit/

echo "\
[theme]\n\
primaryColor='#747c5c'\n\
backgroundColor='#fffcf6'\n\
secondaryBackgroundColor='#e2dfdb'\n\
textColor='#424242'\n\
font='sans serif'\n\
[server]\n\
port = $PORT\n\
enableCORS = false\n\
headless = true\n\
\n\
" > ~/.streamlit/config.toml