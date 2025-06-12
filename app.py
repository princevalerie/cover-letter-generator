# Updated Streamlit app with contact info extraction and fallback input fields
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import docx
import os
from dotenv import load_dotenv
from datetime import datetime
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
import io

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(page_title="Cover Letter Generator", page_icon="📝", layout="wide")

# Gemini API setup
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("❌ GEMINI_API_KEY not found in environment variables!")
    st.stop()

try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"❌ Error configuring Gemini API: {str(e)}")
    st.stop()

# Title and description
st.title("📝 Cover Letter Generator")
st.markdown("Generate professional cover letters using **Gemini 2.0 Flash**")

def extract_text_from_pdf(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def extract_text_from_docx(docx_file):
    try:
        doc = docx.Document(docx_file)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        st.error(f"Error reading DOCX: {e}")
        return ""

def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(uploaded_file)
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(uploaded_file)
    elif uploaded_file.type == "text/plain":
        return str(uploaded_file.read(), "utf-8")
    else:
        st.error("Unsupported file type")
        return ""

def extract_contact_info(text):
    email = re.search(r"[\w\.-]+@[\w\.-]+", text)
    phone = re.search(r"(?<!\d)(\+62|08|62)[\d\s\-]{8,}(?!\d)", text)
    name_lines = text.strip().splitlines()[:10]  # Assume name is at the top
    name = next((line.strip() for line in name_lines if len(line.split()) >= 2 and line[0].isupper()), None)
    return name, email.group() if email else "", phone.group() if phone else ""

def generate_cover_letter(cv_text, job_title, company, job_desc, job_reqs, word_len, name, email, phone, hr_name, hr_role):
    today_date = datetime.now().strftime("%d %B %Y")
    hr_info = f"to {hr_name}, {hr_role}" if hr_name and hr_role else hr_name or "the Hiring Manager"
    prompt = f"""
    Anda adalah seorang penulis surat lamaran profesional yang ahli. Tugas Anda adalah membuat surat lamaran yang menarik, profesional, dan sangat disesuaikan berdasarkan informasi yang diberikan.
    
    **Gunakan tanggal hari ini:** {today_date}
    
    **Informasi Pelamar:**
    - Nama Lengkap: {name}
    - Email: {email}
    - Nomor Telepon: {phone}
    
    **Konten CV (Resume) Pelamar:**
    {cv_text}
    *(Catatan untuk AI: Analisis teks CV ini secara menyeluruh untuk mengidentifikasi pengalaman, keterampilan, pencapaian, dan kualifikasi yang relevan dengan pekerjaan yang dilamar. Jangan hanya menyalin; ekstrak dan sintesis informasi yang paling relevan.)*
    
    **Informasi Pekerjaan:**
    - Judul Posisi: {job_title}
    - Nama Perusahaan: {company}
    - Deskripsi Pekerjaan: {job_desc}
    - Persyaratan Pekerjaan: {job_reqs}
    
    **Informasi Tambahan (Opsional):**
    - Kepada (Penerima Surat/HR): {hr_info} *(Jika kosong, sapa dengan "Dear Hiring Manager," atau "Yth. Tim Rekrutmen,")*
    - Perkiraan Panjang Kata: {word_len} *(Targetkan sekitar angka ini, fleksibilitas +/- 15% diperbolehkan)*
    
    **Panduan Utama Pembuatan Surat Lamaran:**
    
    1.  **Format Surat Profesional:**
        *   **Bagian Kepala:**
            *   Informasi kontak pelamar ({name}, {email}, {phone}) harus jelas di bagian atas.
            *   Tanggal hari ini ({today_date}).
            *   Informasi penerima (jika {hr_info} disediakan dan berisi nama spesifik/jabatan, gunakan itu. Jika tidak, cukup nama perusahaan {company} dan alamat jika ada).
        *   **Salam Pembuka:**
            *   Sapa penerima secara spesifik jika {hr_info} menyediakan nama (misalnya, "Yth. Bapak [Nama Belakang]," atau "Dear Ms. [Last Name],").
            *   Jika {hr_info} kosong, umum (misalnya "Yth. Tim Rekrutmen di {company}," atau "Dear Hiring Manager,"). Hindari "To Whom It May Concern" jika memungkinkan.
        *   **Isi Surat (Konten Inti dan Alur):**
            *   **Awali surat** dengan menyebutkan posisi ({job_title}) yang dilamar dan di mana Anda melihat lowongan tersebut (jika informasi ini ada atau dapat diasumsikan secara umum, misal "website perusahaan"). Nyatakan antusiasme Anda dan secara singkat mengapa Anda yakin merupakan kandidat yang kuat untuk peran tersebut.
            *   **Bagian inti surat harus berfokus pada penyesuaian kualifikasi Anda dengan kebutuhan pekerjaan.** Ini adalah bagian krusial.
                *   Identifikasi 2-3 persyaratan atau tanggung jawab utama dari {job_reqs} dan {job_desc}.
                *   Untuk setiap poin yang diangkat, **tunjukkan, jangan hanya mengatakan.** Jelaskan bagaimana pengalaman, keterampilan, atau pencapaian spesifik dari {cv_text} pelamar secara langsung relevan dan memenuhi persyaratan tersebut. Gunakan contoh konkret dari CV.
                *   **Kuantifikasi pencapaian** jika memungkinkan (misalnya, "berhasil meningkatkan efisiensi proses sebesar 15% dalam 6 bulan").
                *   Tekankan bagaimana kontribusi pelamar dapat **memberikan nilai tambah** bagi {company}.
            *   **(Opsional namun sangat dianjurkan jika informasinya ada atau dapat disimpulkan)** Secara singkat, jelaskan **motivasi khusus** pelamar untuk bergabung dengan {company} (misalnya, ketertarikan pada misi perusahaan, nilai-nilai yang dianut, produk inovatif, atau reputasi industri). Anda juga bisa menyinggung bagaimana pelamar melihat dirinya **cocok dengan budaya perusahaan**, jika ada indikasi.
            *   **Akhiri surat** dengan mengulangi antusiasme Anda untuk posisi tersebut. Sebutkan ketersediaan Anda untuk diskusi lebih lanjut dan sertakan **ajakan bertindak yang sopan dan jelas** (misalnya, "Saya sangat antusias untuk membahas lebih lanjut bagaimana kualifikasi saya dapat mendukung kesuksesan tim Anda di {company}. Terima kasih atas waktu dan pertimbangan Anda.").
        *   **Salam Penutup:** Gunakan penutup profesional seperti "Hormat saya," atau "Sincerely,".
        *   **Tanda Tangan:** Nama lengkap pelamar ({name}).
    
    2.  **Nada dan Gaya:**
        *   **Profesional dan Antusias:** Nada harus menunjukkan kepercayaan diri, profesionalisme, dan antusiasme yang tulus terhadap peran dan perusahaan.
        *   **Bahasa yang Jelas dan Ringkas:** Gunakan bahasa yang mudah dipahami, hindari jargon yang tidak perlu kecuali umum dalam industri tersebut. Kalimat harus efektif dan to the point.
        *   **Proaktif dan Berorientasi pada Solusi:** Bingkai pengalaman sebagai cara Anda memecahkan masalah atau mencapai tujuan.
    
    3.  **Konten yang Disesuaikan (Sangat Penting!):**
        *   **Hindari Pernyataan Generik:** Jangan gunakan frasa klise atau pernyataan umum yang bisa berlaku untuk pekerjaan apa pun (misalnya, "Saya pekerja keras," "Saya pembelajar cepat" tanpa bukti pendukung dari CV).
        *   **Hindari Klaim Berlebihan/Tidak Berdasar:** Semua klaim tentang keterampilan dan pengalaman harus didukung oleh atau dapat disimpulkan dari {cv_text}.
        *   **Fokus pada Kebutuhan Perusahaan:** Surat lamaran harus menunjukkan pemahaman tentang apa yang dicari {company} (berdasarkan {job_desc} dan {job_reqs}) dan bagaimana pelamar dapat memenuhi kebutuhan tersebut.
    
    4.  **Detail Teknis:**
        *   **Gunakan Detail Kontak Nyata:** Pastikan semua detail kontak pelamar ({name}, {email}, {phone}) digunakan secara akurat dan BUKAN placeholder seperti "[Nama Anda]".
        *   **Panjang Kata:** Usahakan mendekati {word_len} kata. Kualitas dan relevansi lebih penting daripada jumlah kata yang kaku.
        *   **Tata Bahasa dan Ejaan:** Pastikan bebas dari kesalahan tata bahasa dan ejaan.
    
    **Output yang Diharapkan:**
    Teks lengkap surat lamaran, siap untuk disalin dan ditempel. Pastikan tidak ada instruksi atau metadata dari prompt ini yang disertakan dalam output akhir.
    """
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text

def create_pdf(text):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=11, leading=14, alignment=TA_JUSTIFY)
    story = [Paragraph(p.strip().replace('\n', ' '), style) for p in text.split('\n\n') if p.strip()]
    story = [Spacer(1, 12) if not isinstance(p, Spacer) else p for p in story]
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- UI STARTS HERE ---
cv_file = st.file_uploader("📄 Upload your CV (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"])

if cv_file:
    cv_text = extract_text_from_file(cv_file)
    name, email, phone = extract_contact_info(cv_text)

    if not name:
        name = st.text_input("Your Name")
    if not email:
        email = st.text_input("Your Email")
    if not phone:
        phone = st.text_input("Your Phone Number")

    job_title = st.text_input("Job Title")
    company = st.text_input("Company Name")
    job_desc = st.text_area("Job Description")
    job_reqs = st.text_area("Job Requirements")
    word_len = st.slider("Word Count", 150, 500, 250, 50)
    hr_name = st.text_input("HR Name (optional)")
    hr_role = st.text_input("HR Role (optional)")

    if st.button("✨ Generate Cover Letter"):
        if all([name, email, phone, job_title, company, job_desc, job_reqs]):
            with st.spinner("Generating cover letter..."):
                result = generate_cover_letter(cv_text, job_title, company, job_desc, job_reqs, word_len, name, email, phone, hr_name, hr_role)
                st.markdown("---")
                st.subheader("📄 Your Cover Letter")
                st.text_area("Preview", result, height=400)
                pdf = create_pdf(result)
                st.download_button("📥 Download PDF", data=pdf, file_name=f"Cover_Letter_{name}.pdf", mime="application/pdf")
        else:
            st.warning("❗ Please complete all required fields.")









# import streamlit as st
# import google.generativeai as genai
# from PyPDF2 import PdfReader
# import docx
# import os
# from dotenv import load_dotenv
# from datetime import datetime
# from reportlab.lib.pagesizes import letter, A4
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib.units import inch
# from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
# import io

# # Load environment variables
# load_dotenv()

# # Configure page
# st.set_page_config(
#     page_title="Cover Letter Generator",
#     page_icon="📝",
#     layout="wide"
# )

# # Configure Gemini API
# api_key = os.getenv("GEMINI_API_KEY")

# # Check if API key exists, if not show error and stop
# if not api_key:
#     st.error("❌ GEMINI_API_KEY not found in environment variables!")
#     st.markdown("""
#     ### 🔧 Setup Required:
    
#     **1. Create a `.env` file in your project root:**
#     ```
#     GEMINI_API_KEY=your_api_key_here
#     ```
    
#     **2. Get your Gemini API Key:**
#     - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
#     - Create a new API key (free)
#     - Copy and paste it to your `.env` file
    
#     **3. Restart the application**
#     """)
#     st.stop()

# try:
#     genai.configure(api_key=api_key)
#     api_configured = True
# except Exception as e:
#     st.error(f"❌ Error configuring Gemini API: {str(e)}")
#     st.stop()

# # Title and description
# st.title("📝 Cover Letter Generator")
# st.markdown("Generate professional cover letters using AI powered by **Gemini 2.0 Flash**")

# # Function to extract text from PDF
# def extract_text_from_pdf(pdf_file):
#     try:
#         pdf_reader = PdfReader(pdf_file)
#         text = ""
#         for page in pdf_reader.pages:
#             text += page.extract_text()
#         return text
#     except Exception as e:
#         st.error(f"Error reading PDF: {str(e)}")
#         return None

# # Function to extract text from DOCX
# def extract_text_from_docx(docx_file):
#     try:
#         doc = docx.Document(docx_file)
#         text = ""
#         for paragraph in doc.paragraphs:
#             text += paragraph.text + "\n"
#         return text
#     except Exception as e:
#         st.error(f"Error reading DOCX: {str(e)}")
#         return None

# # Function to extract text from uploaded file
# def extract_text_from_file(uploaded_file):
#     if uploaded_file is not None:
#         file_type = uploaded_file.type
        
#         if file_type == "application/pdf":
#             return extract_text_from_pdf(uploaded_file)
#         elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
#             return extract_text_from_docx(uploaded_file)
#         elif file_type == "text/plain":
#             return str(uploaded_file.read(), "utf-8")
#         else:
#             st.error("Unsupported file type. Please upload PDF, DOCX, or TXT files.")
#             return None
#     return None

# # Function to create PDF from text
# def create_pdf(text, filename):
#     buffer = io.BytesIO()
#     doc = SimpleDocTemplate(buffer, pagesize=A4, 
#                           rightMargin=72, leftMargin=72,
#                           topMargin=72, bottomMargin=18)
    
#     # Get styles
#     styles = getSampleStyleSheet()
    
#     # Create custom styles
#     title_style = ParagraphStyle(
#         'CustomTitle',
#         parent=styles['Heading1'],
#         fontSize=16,
#         textColor='#333333',
#         spaceAfter=30,
#         alignment=TA_LEFT
#     )
    
#     body_style = ParagraphStyle(
#         'CustomBody',
#         parent=styles['Normal'],
#         fontSize=11,
#         leading=14,
#         textColor='#333333',
#         alignment=TA_JUSTIFY,
#         spaceAfter=12
#     )
    
#     # Build story
#     story = []
    
#     # Split text into paragraphs
#     paragraphs = text.split('\n\n')
    
#     for i, para in enumerate(paragraphs):
#         if para.strip():
#             # Clean the paragraph text for reportlab
#             clean_para = para.strip().replace('\n', ' ')
            
#             # First paragraph gets title style if it looks like a header
#             if i == 0 and (clean_para.startswith('Dear') or len(clean_para) < 100):
#                 story.append(Paragraph(clean_para, body_style))
#             else:
#                 story.append(Paragraph(clean_para, body_style))
            
#             story.append(Spacer(1, 12))
    
#     # Build PDF
#     doc.build(story)
#     buffer.seek(0)
#     return buffer

# # Function to generate cover letter using Gemini 2.0 Flash
# def generate_cover_letter(cv_text, job_description, job_requirements, job_title, company_name, word_length, hr_name=None, hr_role=None):
#     try:
#         # Use Gemini 2.0 Flash model
#         model = genai.GenerativeModel('gemini-2.0-flash')
        
#         # Construct the prompt
#         hr_info = ""
#         if hr_name and hr_role:
#             hr_info = f"Address the cover letter to {hr_name}, {hr_role}."
#         elif hr_name:
#             hr_info = f"Address the cover letter to {hr_name}."
        
#         prompt = f"""
#         You are a professional cover letter writer. Based on the following CV/Resume and job information, create a compelling and personalized cover letter:

#         CV/RESUME CONTENT:
#         {cv_text}

#         JOB INFORMATION:
#         - Job Title: {job_title}
#         - Company Name: {company_name}
#         - Job Description: {job_description}
#         - Job Requirements: {job_requirements}

#         ADDITIONAL INSTRUCTIONS:
#         {hr_info}

#         Always detect my Name,my Phone Number,my Email on CV 

#         Please create a cover letter that:
#         1. Uses proper business letter format with appropriate salutation and closing
#         2. Has a strong opening paragraph that captures attention
#         3. Organizes content in well-structured paragraphs that specifically highlight relevant experience and skills from the CV that match the job requirements
#         4. Directly addresses the specific job requirements mentioned and shows how the candidate meets them
#         5. Shows genuine enthusiasm for the role and demonstrates knowledge about the company
#         6. Includes specific examples and achievements where possible
#         7. Has a compelling closing paragraph with a call to action
#         8. Is professional, engaging, and tailored to the specific role
#         9. Is approximately {word_length} words in length
#         10. Uses active voice and confident language
#         11. Avoids generic statements and clichés
#         12. Maps the candidate's qualifications to the specific requirements listed
#         13. Don't use self claim words like (iam proficient in ),etc..focus on impact on my CV to make it stand out
#         14. Always mention something in my cv that allign with job description or minimun requirement, but don't make it up something that don't exist on my cv

#         Format the cover letter with:
#         - Input my Name,my Phone Number,my Email on cover letter
#         - Date right now
#         - Professional salutation
#         - Well-structured paragraphs (you decide the optimal number and structure)
#         - Professional closing and signature line

#         Make it sound authentic and compelling while maintaining professionalism. Focus especially on how the candidate's background aligns with the specific requirements mentioned. Structure the paragraphs in the most effective way to present the candidate's qualifications.
#         """
        
#         response = model.generate_content(prompt)
#         return response.text
    
#     except Exception as e:
#         st.error(f"Error generating cover letter: {str(e)}")
#         return None

# # Sidebar with information
# with st.sidebar:
#     st.success("🔑 API Key loaded from .env")
        
#     st.markdown("---")
#     st.header("ℹ️ About")
#     st.markdown("**Powered by Gemini 2.0 Flash**")
#     st.markdown("This tool generates personalized cover letters by analyzing your CV and the job requirements.")
    
#     st.markdown("---")
#     st.header("📋 How to Use")
#     st.markdown("""
#     1. **Upload your CV/Resume**
#     2. **Enter job title & company**
#     3. **Add job description & requirements**
#     4. **Set word count preference**
#     5. **Add HR info** (optional)
#     6. **Click Generate**
#     7. **Download as TXT or PDF**
#     """)
    
#     st.markdown("---")
#     st.header("💝 Tips")
#     st.markdown("""
#     • Use a detailed CV with specific achievements
#     • Provide complete job description
#     • List specific requirements separately
#     • Adjust word count based on company preference
#     • Include technical skills and qualifications
#     • Add company-specific information
#     • Review and customize the output
#     """)

# # Create two columns
# col1, col2 = st.columns([1, 1])

# with col1:
#     st.header("📋 Input Information")
    
#     # File uploader for CV/Resume
#     uploaded_file = st.file_uploader(
#         "Upload your CV/Resume",
#         type=['pdf', 'docx', 'txt'],
#         help="Supported formats: PDF, DOCX, TXT"
#     )
    
#     # Extract text from uploaded file
#     cv_text = ""
#     if uploaded_file:
#         with st.spinner("Extracting text from file..."):
#             cv_text = extract_text_from_file(uploaded_file)
#             if cv_text:
#                 st.success("✅ CV/Resume uploaded successfully!")
#                 with st.expander("Preview extracted text"):
#                     st.text_area("Extracted Content", cv_text[:500] + "..." if len(cv_text) > 500 else cv_text, height=150, disabled=True)
    
#     # Job information inputs
#     st.subheader("Job Information")
#     job_title = st.text_input(
#         "Job Title/Role *", 
#         placeholder="e.g., Senior Software Engineer",
#         help="Enter the exact job title from the job posting"
#     )
#     company_name = st.text_input(
#         "Company Name *", 
#         placeholder="e.g., Google Indonesia",
#         help="Enter the full company name"
#     )
#     job_description = st.text_area(
#         "Job Description *", 
#         placeholder="Paste the complete job description here including responsibilities and qualifications...",
#         height=150,
#         help="Include the full job posting for best results"
#     )
    
#     job_requirements = st.text_area(
#         "Job Requirements *", 
#         placeholder="List the specific requirements, skills, qualifications, and experience needed for this role...",
#         height=150,
#         help="Include technical skills, years of experience, education requirements, certifications, etc."
#     )
    
#     # Optional HR information
#     st.subheader("HR Information (Optional)")
#     col_hr1, col_hr2 = st.columns(2)
#     with col_hr1:
#         hr_name = st.text_input("HR Name", placeholder="e.g., Sarah Johnson")
#     with col_hr2:
#         hr_role = st.text_input("HR Role", placeholder="e.g., HR Manager")
    
#     # Word length control
#     st.subheader("Cover Letter Settings")
#     word_length = st.slider(
#         "Target Word Count", 
#         min_value=20, 
#         max_value=600, 
#         value=350, 
#         step=10,
#         help="Choose the approximate length of your cover letter"
#     )
    
#     # Generate button
#     generate_btn = st.button("🚀 Generate Cover Letter", type="primary", use_container_width=True)

# with col2:
#     st.header("📄 Generated Cover Letter")
    
#     # Check if all required fields are filled
#     if generate_btn:
#         if not cv_text:
#             st.error("❌ Please upload your CV/Resume first!")
#         elif not job_title:
#             st.error("❌ Please enter the job title!")
#         elif not company_name:
#             st.error("❌ Please enter the company name!")
#         elif not job_description:
#             st.error("❌ Please enter the job description!")
#         elif not job_requirements:
#             st.error("❌ Please enter the job requirements!")
#         else:
#             with st.spinner("🤖 AI is crafting your personalized cover letter..."):
#                 cover_letter = generate_cover_letter(
#                     cv_text, job_description, job_requirements, job_title, company_name, word_length, hr_name, hr_role
#                 )
                
#                 if cover_letter:
#                     st.success("✅ Cover letter generated successfully!")
                    
#                     # Store in session state for persistence
#                     st.session_state.cover_letter = cover_letter
#                     st.session_state.company_name = company_name
#                     st.session_state.job_title = job_title

#     # Display cover letter if it exists in session state
#     if 'cover_letter' in st.session_state:
#         cover_letter = st.session_state.cover_letter
#         company_name = st.session_state.company_name
#         job_title = st.session_state.job_title
        
#         # Display the cover letter
#         st.text_area(
#             "Your Cover Letter:",
#             cover_letter,
#             height=600,
#             key="cover_letter_output"
#         )
        
#         # Action buttons
#         col_btn1, col_btn2, col_btn3 = st.columns(3)
        
#         with col_btn1:
#             # Download TXT button
#             st.download_button(
#                 label="📥 Download TXT",
#                 data=cover_letter,
#                 file_name=f"cover_letter_{company_name.replace(' ', '_')}_{job_title.replace(' ', '_')}.txt",
#                 mime="text/plain",
#                 use_container_width=True
#             )
        
#         with col_btn2:
#             # Download PDF button
#             try:
#                 pdf_buffer = create_pdf(cover_letter, f"cover_letter_{company_name}_{job_title}")
#                 st.download_button(
#                     label="📑 Download PDF",
#                     data=pdf_buffer,
#                     file_name=f"cover_letter_{company_name.replace(' ', '_')}_{job_title.replace(' ', '_')}.pdf",
#                     mime="application/pdf",
#                     use_container_width=True
#                 )
#             except Exception as e:
#                 st.error(f"PDF generation error: {str(e)}")
#                 st.info("💡 Install reportlab: `pip install reportlab`")
        
#         with col_btn3:
#             # Copy to clipboard info
#             if st.button("📋 Show for Copy", use_container_width=True):
#                 st.code(cover_letter, language=None)
#                 st.info("💡 Select the text above and copy it (Ctrl+C / Cmd+C)")
        
#         # Additional options
#         st.markdown("---")
#         st.subheader("📊 Document Statistics")
#         words = len(cover_letter.split())
#         chars = len(cover_letter)
#         col_stat1, col_stat2, col_stat3 = st.columns(3)
#         with col_stat1:
#             st.metric("Words", words)
#         with col_stat2:
#             st.metric("Characters", chars)
#         with col_stat3:
#             st.metric("Paragraphs", cover_letter.count('\n\n') + 1)
#     else:
#         # Default view when no generation is done
#         st.info("👈 Fill in the information on the left and click 'Generate Cover Letter' to create your personalized cover letter.")
        
#         # Show example preview
#         st.subheader("📄 Sample Output Preview")
#         st.markdown("""
#         Your generated cover letter will appear here with:
        
#         ✅ **Professional format** with proper business letter structure  
#         ✅ **Personalized content** based on your CV and job requirements  
#         ✅ **Compelling opening** that captures attention  
#         ✅ **Relevant experience** highlighting your best qualifications  
#         ✅ **Requirements mapping** showing how you meet specific job requirements  
#         ✅ **Company-specific** details showing genuine interest  
#         ✅ **Strong closing** with clear call to action  
#         """)

