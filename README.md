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


Como usar o generate_study_materials.py (Gera quizzes e flashcards) : \
# Com PDF
python scripts/generate_study_materials.py notas_biologia.pdf

# Com imagem
python scripts/generate_study_materials.py lecture_slide.jpg

# Com texto direto
python scripts/generate_study_materials.py --text "A mitocôndria é a powerhouse da célula..."

# Com ficheiro TXT
python scripts/generate_study_materials.py resumo.txt

# Personalizar número de flashcards e questões
python scripts/generate_study_materials.py biology.pdf --cards 20 --quiz 15

# Filtrar por dificuldade
python scripts/generate_study_materials.py biology.pdf --difficulty easy

# Gerar apenas flashcards (sem quiz)
python scripts/generate_study_materials.py biology.pdf --no-quiz

# Gerar apenas quiz (sem flashcards)
python scripts/generate_study_materials.py biology.pdf --no-flashcards

# Mudar diretório de output
python scripts/generate_study_materials.py biology.pdf --output-dir meus_resultados
## source capstone/bin/activate


****Proximos passos:
   1. Abre os ficheiros JSON para ver os resultados completos
   2. Importa para a tua app React
   3. Ou usa como referencia para criar API