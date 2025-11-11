# ILM Geo-INQUIRE Dashboard

## Overview
Professional Implementation Level Matrix (ILM) Dashboard for the Geo-INQUIRE project at the University of Bergen.

## Features
- 🔐 Password-protected access
- 📊 Real-time data integration with Google Sheets
- 📈 Comprehensive Virtual Access and Transnational Access analytics
- 🎯 KPI tracking and monitoring
- 💾 Professional chart exports (300 DPI)

## Installation

### Prerequisites
- Python 3.8 or higher
- Google Sheets API credentials

### Setup
1. Clone this repository
   ```bash
   git clone https://github.com/YOUR_USERNAME/ilm-dashboard.git
   cd ilm-dashboard
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Add your Google Sheets credentials
   - Get your service account JSON file from Google Cloud Console
   - Place it in the project folder
   - Or configure secrets (for Streamlit Cloud deployment)

4. Run the dashboard
   ```bash
   streamlit run ilm_dashboard_app_v2_FINAL.py
   ```

## Usage

### Login
- Password: Contact project administrator

### Navigation
- **Dashboard** - Overview and key metrics
- **Analytics** - Detailed analysis and trends
- **KPI** - Key Performance Indicators
- **Data** - Raw data tables
- **Contact** - Project information

### Switching Projects
Use the sidebar to toggle between:
- Virtual Access
- Transnational Access

## Data Sources
- **Primary:** Google Sheets (auto-refresh every 5 minutes)
- **Fallback:** Excel file (ILM_Python_2.xlsx)

## Deployment

### Streamlit Community Cloud
1. Push code to GitHub
2. Sign up at https://streamlit.io/cloud
3. Connect your repository
4. Configure secrets (Google Sheets credentials)
5. Deploy!

See `STREAMLIT_DEPLOYMENT_GUIDE.md` for detailed instructions.

## Documentation
- `FINAL_DELIVERY_SUMMARY.md` - Complete overview
- `GIT_DEPLOYMENT_GUIDE.md` - Git setup and workflow
- `STREAMLIT_DEPLOYMENT_GUIDE.md` - Cloud deployment
- `QUICK_REFERENCE.md` - Quick tips and solutions

## Development

### Project Structure
```
ilm-dashboard/
├── ilm_dashboard_app_v2_FINAL.py    # Main application
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
├── .gitignore                        # Git ignore rules
└── .streamlit/                       # Streamlit configuration
    └── secrets.toml                  # Credentials (not in Git!)
```

### Making Changes
1. Create a feature branch
   ```bash
   git checkout -b feature/your-feature
   ```

2. Make your changes

3. Test locally
   ```bash
   streamlit run ilm_dashboard_app_v2_FINAL.py
   ```

4. Commit and push
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin feature/your-feature
   ```

5. Create Pull Request on GitHub

## Security
- ⚠️ Never commit credentials (.json files)
- ⚠️ Keep `.gitignore` up to date
- ⚠️ Use Streamlit secrets for cloud deployment
- ⚠️ Rotate credentials regularly

## Copyright
© 2024-2025 Geo-INQUIRE Project  
University of Bergen, Norway

Developed by: Juliano and Claude AI Assistant

## License
Internal use - Geo-INQUIRE Project

## Contact
Geo-INQUIRE Project Administration  
University of Bergen, Norway

## Version
**Version:** 2.0 FINAL  
**Last Updated:** November 11, 2025

## Support
For issues or questions:
- Check documentation in `/docs` folder
- Review troubleshooting guides
- Contact project administrator

---

**Ready to deploy?** See `STREAMLIT_DEPLOYMENT_GUIDE.md` to get started! 🚀
