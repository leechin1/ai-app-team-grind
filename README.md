# Let's start actual development of the Capstone Project

## Phase 1: Setting up the note ingestion part
How will this happen? That is a very interesting question.

Use case 1: User writes a file with built in terminal. Considerations:
- i. He should be able to write the file in a text editor = there needs to be a text editor
- ii. User might want to paste images (I am very lazy and like to do that because typing is a lot of effort)

Solution: 
- i. User writes file as markdown as file is stored in a row as markdown (varchar) in supabase. Very good practice for sanitization.
- ii. A dedicated section to just paste images (which are stored in supabase bucket)

R&D
https://www.surajon.dev/how-to-build-a-markdown-blog-with-nextjs-supabase-and-chakra-ui [ı]
https://github.com/marketplace/actions/markdown-to-supabase [i]
https://discuss.streamlit.io/t/new-component-streamlit-paste-button-effortless-image-pasting-in-your-streamlit-apps/58978 [ii]
https://community.weweb.io/t/displaying-an-image-from-supabase/5630/12 [iii]

Use case 2: User uploads a PDF
- i. User uploads a PDF or image. But yeah i guess it should then render as markdown just for storage to be easier


Solution:
- i. Just bucket it or just parse it as markdonw?

Okay let's run some tests on the best way to parse documents.
(...)
### Overall consensus:
For use cases of user writing or uploading:
- File is parsed to markdown. PDFs will automatically lose pictures
Tool: Docling Vision Models

Data types accepted for upload: pdf

Current proto: Intakes PDF file (ONLY) and converts to markdown with docling vision