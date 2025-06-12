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

# Function to validate API key
def validate_api_key(api_key):
    """Validate if the API key is working by making a simple test call"""
    try:
        if not api_key or not api_key.startswith('AIza'):
            return False, "API key should start with 'AIza'"
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Make a simple test call
        response = model.generate_content("Hello")
        return True, "API key is valid"
    except Exception as e:
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg:
            return False, "Invalid API key. Please check your key."
        elif "PERMISSION_DENIED" in error_msg:
            return False, "API key doesn't have permission for Gemini API."
        elif "QUOTA_EXCEEDED" in error_msg:
            return False, "API quota exceeded. Please check your usage."
        else:
            return False, f"Error: {error_msg}"

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
            with st.spinner("Validating API key..."):
                is_valid, message = validate_api_key(api_key)
                if is_valid:
                    st.success(f"✅ {message}")
                    api_configured = True
                else:
                    st.error(f"❌ {message}")
        else:
            st.info("Please enter your API key to continue")
        
        st.markdown("---")
        st.markdown("### 🔗 How to get Gemini API Key:")
        st.markdown("1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)")
        st.markdown("2. Create a new API key (free)")
        st.markdown("3. Copy and paste it above")
        st.markdown("4. Or add it to your .env file as GEMINI_API_KEY")
        
        st.markdown("---")
        st.markdown("### 🔧 Troubleshooting:")
        st.markdown("""
        **Common Issues:**
        - API key should start with 'AIza'
        - Make sure you copied the complete key
        - Check if Gemini API is enabled in your Google Cloud project
        - Verify your API quota hasn't been exceeded
        """)
else:
    with st.spinner("Validating API key from .env..."):
        is_valid, message = validate_api_key(api_key)
        if is_valid:
            api_configured = True
        else:
            st.error(f"❌ {message}")
            st.error("Please check your .env file or enter a valid API key in the sidebar")
            
            # Show sidebar for manual input as fallback
            with st.sidebar:
                st.header("🔑 API Configuration")
                st.error("Invalid API key in .env file")
                api_key_manual = st.text_input("Enter a valid Gemini API Key", type="password", key="api_key_manual")
                
                if api_key_manual:
                    with st.spinner("Validating manual API key..."):
                        is_valid_manual, message_manual = validate_api_key(api_key_manual)
                        if is_valid_manual:
                            st.success(f"✅ {message_manual}")
                            api_configured = True
                            api_key = api_key_manual  # Use manual key
                        else:
                            st.error(f"❌ {message_manual}")
                
                st.markdown("---")
                st.markdown("### 🔗 Get a new API Key:")
                st.markdown("1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)")
                st.markdown("2. Create a new API key")
                st.markdown("3. Make sure to enable Gemini API access")

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
def generate_cover_letter(cv_text, job_description, job_title, company_name, hr_name=None, hr_role=None, requirements=None):
    try:
        # Use Gemini 2.0 Flash model
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Construct the prompt
        hr_info = ""
        if hr_name and hr_role:
            hr_info = f"Address the cover letter to {hr_name}, {hr_role}."
        elif hr_name:
            hr_info = f"Address the cover letter to {hr_name}."
        
        requirements_info = ""
        if requirements and requirements.strip():
            requirements_info = f"""
        ADDITIONAL REQUIREMENTS TO HIGHLIGHT:
        {requirements}
        
        Please make sure to specifically address these requirements in the cover letter.
        """
        
        prompt = f"""
        You are a professional cover letter writer. Based on the following CV/Resume and job information, create a compelling and personalized cover letter:

        CV/RESUME CONTENT:
        {cv_text}

        JOB INFORMATION:
        - Job Title: {job_title}
        - Company Name: {company_name}
        - Job Description: {job_description}

        {requirements_info}

        ADDITIONAL INSTRUCTIONS:
        {hr_info}

        Please create a cover letter that:
        1. Uses proper business letter format with appropriate salutation and closing
        2. Has a strong opening paragraph that captures attention
        3. Body paragraphs (2-3) that specifically highlight relevant experience and skills from the CV that match the job requirements
        4. Shows genuine enthusiasm for the role and demonstrates knowledge about the company
        5. Includes specific examples and achievements where possible
        6. Addresses any additional requirements mentioned above
        7. Has a compelling closing paragraph with a call to action
        8. Is professional, engaging, and tailored to the specific role
        9. Is approximately 250-400 words in length
        10. Uses active voice and confident language
        11. Avoids generic statements and clichés

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
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg:
            st.error("❌ **API Key Error**: Your API key is invalid or expired.")
            st.error("**Solutions:**")
            st.error("1. Check if your API key is correct (should start with 'AIza')")
            st.error("2. Generate a new API key from Google AI Studio")
            st.error("3. Make sure Gemini API is enabled in your project")
        elif "PERMISSION_DENIED" in error_msg:
            st.error("❌ **Permission Error**: API key doesn't have access to Gemini API.")
            st.error("Make sure to enable Gemini API access in Google AI Studio")
        elif "QUOTA_EXCEEDED" in error_msg:
            st.error("❌ **Quota Error**: API usage limit exceeded.")
            st.error("Please check your API usage or upgrade your plan")
        elif "gemini-2.0-flash-exp" in error_msg.lower():
            st.warning("⚠️ **Model Error**: Gemini 2.0 Flash Experimental might not be available.")
            st.info("Trying with Gemini Pro instead...")
            try:
                # Fallback to gemini-pro
                model_fallback = genai.GenerativeModel('gemini-pro')
                response = model_fallback.generate_content(prompt)
                st.success("✅ Generated using Gemini Pro (fallback)")
                return response.text
            except Exception as fallback_error:
                st.error(f"❌ Fallback also failed: {str(fallback_error)}")
                return None
        else:
            st.error(f"❌ **Unexpected Error**: {error_msg}")
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
        4. **Specify requirements** (optional)
        5. **Click Generate**
        6. **Download or copy** your cover letter
        """)
        
        st.markdown("---")
        st.header("💝 Tips")
        st.markdown("""
        • Use a detailed CV with specific achievements
        • Provide complete job description
        • Include company-specific information
        • Add specific requirements you want emphasized
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
    
    # Additional Requirements
    st.subheader("Additional Requirements (Optional)")
    requirements = st.text_area(
        "Specific Requirements to Highlight",
        placeholder="Enter any specific requirements, skills, or qualifications you want to emphasize in your cover letter...\n\nExample:\n- 5+ years experience in React\n- Strong leadership skills\n- Experience with Agile methodology",
        height=120,
        help="Add any specific points you want to emphasize that might not be fully covered in the job description"
    )
    
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
                    cv_text, job_description, job_title, company_name, hr_name, hr_role, requirements
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

with st.expander("🔑 API Key Setup & Troubleshooting"):
    st.markdown("""
    **Get your free Gemini API key:**
    1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
    2. Sign in with your Google account
    3. Click "Create API Key" → "Create API key in new project"
    4. Copy the generated key (starts with 'AIza')
    5. Add it to your `.env` file or enter manually in sidebar
    
    **Common Issues & Solutions:**
    
    ❌ **"API key not valid"**
    - Make sure you copied the complete API key
    - API key should start with 'AIza'
    - Generate a new key if the old one expired
    
    ❌ **"Permission denied"**  
    - Enable Gemini API access in Google AI Studio
    - Make sure you're using the correct Google account
    
    ❌ **"Quota exceeded"**
    - Check your API usage limits
    - Wait for quota reset or upgrade plan
    
    ❌ **"Model not available"**
    - App will automatically fallback to Gemini Pro
    - Some experimental models may have limited availability
    
    **Note:** Gemini API offers generous free tier limits for testing and development.
    """)

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Made with ❤️ using Streamlit and Gemini AI | 
    <a href='https://github.com' target='_blank'>View Source Code</a></p>
</div>
""", unsafe_allow_html=True)
