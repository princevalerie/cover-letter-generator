import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import docx
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Cover Letter Generator",
    page_icon="📝",
    layout="wide"
)

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
api_configured = False

if not api_key:
    # Show sidebar for API key input if not found in environment
    with st.sidebar:
        st.header("🔑 API Configuration")
        st.warning("API key not found in .env file")
        api_key = st.text_input("Enter your Gemini API Key", type="password", key="api_key_input")
        
        if api_key:
            try:
                genai.configure(api_key=api_key)
                st.success("✅ API Key configured!")
                api_configured = True
            except Exception as e:
                st.error(f"❌ Invalid API key: {str(e)}")
        else:
            st.info("Please enter your API key to continue")
        
        st.markdown("---")
        st.markdown("### 🔗 How to get Gemini API Key:")
        st.markdown("1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)")
        st.markdown("2. Create a new API key (free)")
        st.markdown("3. Copy and paste it above")
        st.markdown("4. Or add it to your .env file as GEMINI_API_KEY")
else:
    try:
        genai.configure(api_key=api_key)
        api_configured = True
    except Exception as e:
        st.error(f"❌ Error configuring Gemini API: {str(e)}")
        st.stop()

# Title and description
st.title("📝 Cover Letter Generator")
st.markdown("Generate professional cover letters using AI powered by **Gemini 2.0 Flash**")

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

# Function to extract text from DOCX
def extract_text_from_docx(docx_file):
    try:
        doc = docx.Document(docx_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading DOCX: {str(e)}")
        return None

# Function to extract text from uploaded file
def extract_text_from_file(uploaded_file):
    if uploaded_file is not None:
        file_type = uploaded_file.type
        
        if file_type == "application/pdf":
            return extract_text_from_pdf(uploaded_file)
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return extract_text_from_docx(uploaded_file)
        elif file_type == "text/plain":
            return str(uploaded_file.read(), "utf-8")
        else:
            st.error("Unsupported file type. Please upload PDF, DOCX, or TXT files.")
            return None
    return None

# Function to generate cover letter using Gemini 2.0 Flash
def generate_cover_letter(cv_text, job_description, job_title, company_name, hr_name=None, hr_role=None):
    try:
        # Use Gemini 2.0 Flash model
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Construct the prompt
        hr_info = ""
        if hr_name and hr_role:
            hr_info = f"Address the cover letter to {hr_name}, {hr_role}."
        elif hr_name:
            hr_info = f"Address the cover letter to {hr_name}."
        
        prompt = f"""
        You are a professional cover letter writer. Based on the following CV/Resume and job information, create a compelling and personalized cover letter:

        CV/RESUME CONTENT:
        {cv_text}

        JOB INFORMATION:
        - Job Title: {job_title}
        - Company Name: {company_name}
        - Job Description: {job_description}

        ADDITIONAL INSTRUCTIONS:
        {hr_info}

        Please create a cover letter that:
        1. Uses proper business letter format with appropriate salutation and closing
        2. Has a strong opening paragraph that captures attention
        3. Body paragraphs (2-3) that specifically highlight relevant experience and skills from the CV that match the job requirements
        4. Shows genuine enthusiasm for the role and demonstrates knowledge about the company
        5. Includes specific examples and achievements where possible
        6. Has a compelling closing paragraph with a call to action
        7. Is professional, engaging, and tailored to the specific role
        8. Is approximately 250-400 words in length
        9. Uses active voice and confident language
        10. Avoids generic statements and clichés

        Format the cover letter with:
        - Proper date
        - Recipient address (if HR info provided)
        - Professional salutation
        - Well-structured body paragraphs
        - Professional closing and signature line

        Make it sound authentic and compelling while maintaining professionalism.
        """
        
        response = model.generate_content(prompt)
        return response.text
    
    except Exception as e:
        st.error(f"Error generating cover letter: {str(e)}")
        return None

# Sidebar with information (only show if API is configured)
if api_configured:
    with st.sidebar:
        if os.getenv("GEMINI_API_KEY"):
            st.success("🔑 API Key loaded from .env")
        else:
            st.success("🔑 API Key configured manually")
            
        st.markdown("---")
        st.header("ℹ️ About")
        st.markdown("**Powered by Gemini 2.0 Flash**")
        st.markdown("This tool generates personalized cover letters by analyzing your CV and the job requirements.")
        
        st.markdown("---")
        st.header("📋 How to Use")
        st.markdown("""
        1. **Upload your CV/Resume**
        2. **Enter job details**
        3. **Add HR info** (optional)
        4. **Click Generate**
        5. **Download or copy** your cover letter
        """)
        
        st.markdown("---")
        st.header("💝 Tips")
        st.markdown("""
        • Use a detailed CV with specific achievements
        • Provide complete job description
        • Include company-specific information
        • Review and customize the output
        """)

# Main interface - only show if API is configured
if not api_configured:
    st.warning("👈 Please configure your Gemini API key in the sidebar to continue.")
    st.info("**Option 1:** Add `GEMINI_API_KEY=your_key_here` to your `.env` file")
    st.info("**Option 2:** Enter your API key in the sidebar")
    st.stop()

# Create two columns
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📋 Input Information")
    
    # File uploader for CV/Resume
    uploaded_file = st.file_uploader(
        "Upload your CV/Resume",
        type=['pdf', 'docx', 'txt'],
        help="Supported formats: PDF, DOCX, TXT"
    )
    
    # Extract text from uploaded file
    cv_text = ""
    if uploaded_file:
        with st.spinner("Extracting text from file..."):
            cv_text = extract_text_from_file(uploaded_file)
            if cv_text:
                st.success("✅ CV/Resume uploaded successfully!")
                with st.expander("Preview extracted text"):
                    st.text_area("Extracted Content", cv_text[:500] + "..." if len(cv_text) > 500 else cv_text, height=150, disabled=True)
    
    # Job information inputs
    st.subheader("Job Information")
    job_title = st.text_input(
        "Job Title/Role *", 
        placeholder="e.g., Senior Software Engineer",
        help="Enter the exact job title from the job posting"
    )
    company_name = st.text_input(
        "Company Name *", 
        placeholder="e.g., Google Indonesia",
        help="Enter the full company name"
    )
    job_description = st.text_area(
        "Job Description *", 
        placeholder="Paste the complete job description here including requirements, responsibilities, and qualifications...",
        height=200,
        help="Include the full job posting for best results"
    )
    
    # Optional HR information
    st.subheader("HR Information (Optional)")
    col_hr1, col_hr2 = st.columns(2)
    with col_hr1:
        hr_name = st.text_input("HR Name", placeholder="e.g., Sarah Johnson")
    with col_hr2:
        hr_role = st.text_input("HR Role", placeholder="e.g., HR Manager")
    
    # Generate button
    generate_btn = st.button("🚀 Generate Cover Letter", type="primary", use_container_width=True)

with col2:
    st.header("📄 Generated Cover Letter")
    
    # Check if all required fields are filled
    if generate_btn:
        if not cv_text:
            st.error("❌ Please upload your CV/Resume first!")
        elif not job_title:
            st.error("❌ Please enter the job title!")
        elif not company_name:
            st.error("❌ Please enter the company name!")
        elif not job_description:
            st.error("❌ Please enter the job description!")
        else:
            with st.spinner("🤖 AI is crafting your personalized cover letter..."):
                cover_letter = generate_cover_letter(
                    cv_text, job_description, job_title, company_name, hr_name, hr_role
                )
                
                if cover_letter:
                    st.success("✅ Cover letter generated successfully!")
                    
                    # Display the cover letter
                    st.text_area(
                        "Your Cover Letter:",
                        cover_letter,
                        height=600,
                        key="cover_letter_output"
                    )
                    
                    # Action buttons
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        # Download button
                        st.download_button(
                            label="📥 Download as TXT",
                            data=cover_letter,
                            file_name=f"cover_letter_{company_name.replace(' ', '_')}_{job_title.replace(' ', '_')}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    
                    with col_btn2:
                        # Copy to clipboard info
                        if st.button("📋 Show for Copy", use_container_width=True):
                            st.code(cover_letter, language=None)
                            st.info("💡 Select the text above and copy it (Ctrl+C / Cmd+C)")
                    
                    # Additional options
                    st.markdown("---")
                    st.subheader("📊 Document Statistics")
                    words = len(cover_letter.split())
                    chars = len(cover_letter)
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    with col_stat1:
                        st.metric("Words", words)
                    with col_stat2:
                        st.metric("Characters", chars)
                    with col_stat3:
                        st.metric("Paragraphs", cover_letter.count('\n\n') + 1)

# Default view when no generation is done
if not generate_btn and col2:
    with col2:
        st.info("👈 Fill in the information on the left and click 'Generate Cover Letter' to create your personalized cover letter.")
        
        # Show example preview
        st.subheader("📄 Sample Output Preview")
        st.markdown("""
        Your generated cover letter will appear here with:
        
        ✅ **Professional format** with proper business letter structure  
        ✅ **Personalized content** based on your CV and job requirements  
        ✅ **Compelling opening** that captures attention  
        ✅ **Relevant experience** highlighting your best qualifications  
        ✅ **Company-specific** details showing genuine interest  
        ✅ **Strong closing** with clear call to action  
        """)

# Footer
st.markdown("---")
st.markdown("### 🔧 Setup Instructions")

with st.expander("📦 Installation & Setup Guide"):
    st.markdown("""
    **1. Install Required Dependencies:**
    ```bash
    pip install streamlit google-generativeai PyPDF2 python-docx python-dotenv
    ```
    
    **2. Create .env file:**
    Create a `.env` file in your project root with your Gemini API key.
    
    **3. Run the Application:**
    ```bash
    streamlit run app.py
    ```
    """)

with st.expander("🔑 API Key Setup"):
    st.markdown("""
    **Get your free Gemini API key:**
    1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
    2. Click "Create API Key"
    3. Copy the generated key
    4. Add it to your `.env` file
    
    **Note:** Gemini 2.0 Flash offers improved performance and better understanding compared to previous versions.
    """)

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Made with ❤️ using Streamlit and Gemini 2.0 Flash | 
    <a href='https://github.com' target='_blank'>View Source Code</a></p>
</div>
""", unsafe_allow_html=True)
