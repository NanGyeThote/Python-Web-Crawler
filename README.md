# Image Downloader Pro

This application is a simple yet powerful tool for downloading images from the web. It features a user-friendly graphical interface built with Tkinter and supports various image search engines.

## Features

*   **Multiple Search Engines:** Choose from Google, Google API, and Unsplash to find the images you need.
*   **Customizable Downloads:** Specify the number of images to download, the image type (JPG, PNG), and the destination folder.
*   **Image Preview:** View thumbnails of the downloaded images.
*   **Error Logging:** Keep track of any issues that occur during the download process.

## Setup and Usage

1.  **Prerequisites:**
    *   Python 3.x
    *   Pip (Python package installer)

2.  **Installation:**
    *   Clone this repository or download the source code.
    *   Install the required Python packages using pip:
        ```bash
        pip install -r requirements.txt
        ```

3.  **API Key Configuration:**
    *   This application uses the Google Custom Search API and the Unsplash API for image searches. To use these services, you will need to obtain API keys and configure them as environment variables.
    *   Create a `.env` file in the project's root directory and add the following lines, replacing the placeholder values with your actual API keys:
        ```
        GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
        GOOGLE_CSE_ID="YOUR_GOOGLE_CSE_ID"
        UNSPLASH_ACCESS_KEY="YOUR_UNSPLASH_ACCESS_KEY"
        ```

4.  **Running the Application:**
    *   Execute the `web_crawler.py` script to launch the application:
        ```bash
        python web_crawler.py
        ```

## Search Engines

*   **Google:** This option scrapes Google Images for search results. It is a free and easy way to find images, but it may not always provide the highest quality results.
*   **Google API:** This option uses the Google Custom Search API to retrieve high-resolution images. It is a more reliable and powerful option than the standard Google search, but it requires an API key and may incur costs depending on your usage.
*   **Unsplash:** This option uses the Unsplash API to download high-quality, royalty-free images. It is a great option for finding beautiful and unique images, but it requires an API key.
