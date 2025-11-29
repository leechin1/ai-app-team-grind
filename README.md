What you guys have to do to run this

0- Create a venv. Comman in terminal: python -m venv capstone

0- Set up in a .env file your GEMINI_API|_KEY

1- Run requirements. Command in terminal: pip install -r requirements.txt

2- To run the file in browser: Comman in terminal: streamlit run hero.py (hero is our learning page)


Basically what we need:
- Better interface/ database storage: I am working on it
- Someone to do the LLM part: aka smart note generation + flashcards + quizz generator with a nice interface
- RAG Q&A feature
- User cases diagrams + Platform architecture

To improove : 
1. in the core/ai_generator.py : - System prompt 
                              - json output like in the classes
                              - temperature like the classes
                              - vereficar _call_gemini_with_retry e helper methods
  
2. Give ai tools like : - an ML model to improve handwriting recognitions 
                        - In the document processor give gemini TeX and math outuput in a pdf \
                        - convert math handwriting in a LaTex like pdf with math symbols
                        - search other tools to give to the Gemini 

3. 
## source capstone/bin/activate
