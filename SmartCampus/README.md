# Book Market Analytics – Books to Scrape

**Student Name:** Fulufhelo Mulaudzi  
**Student Number:** 402601594    
**Module:** Data Science 500  
**Institution:** Richfield Graduate Institution  

---

## Project Overview
This project is an end-to-end data science workflow built on **Books to Scrape** (books.toscrape.com), a sandbox website designed for web scraping practice. It scrapes the full catalogue of 1,000 books, cleans the data, explores price and rating patterns, and builds a **linear regression model** that tries to predict book price. The findings are written up in a short consulting-style report.

**Business question:** *Which publicly visible book attributes (rating, genre, stock level, title and description features) are associated with a book's price, and can a linear regression predict price from them?*

The notebook follows the **five steps of data science** from the Data Science 500 study guide:

| Step (study guide) | Where it is in the notebook |
| :--- | :--- |
| 1. Asking an interesting question | Title cell (business question) |
| 2. Obtaining the data | Web scraping with `requests` and BeautifulSoup |
| 3. Exploring the data | Cleaning and preparation, then visualisation |
| 4. Modelling the data | Linear regression |
| 5. Communicating and visualising results | Written report generated as a PDF |

---

## What the Project Does

### 1. Data Acquisition (Web Scraping)
*   Uses **requests** and **BeautifulSoup** to scrape all 50 listing pages (20 books each).
*   Visits every book's detail page to collect the stock quantity, genre, description and UPC.
*   Extracts the title, price (GBP), star rating (as a word, One to Five), and stock availability for each book.
*   Sets a User-Agent header, pauses politely between requests, uses `try/except` error handling, and counts and reports any failed pages.

### 2. Data Cleaning
*   Converts prices such as `£51.77` into numbers.
*   Converts rating words (`One` to `Five`) into 1 to 5.
*   Extracts the stock quantity from text such as `In stock (22 available)`.
*   Removes duplicate books (by UPC) and keeps books with missing descriptions (2 in this dataset), flagged with `has_description`.
*   Creates new features: title length, title word count, description length and description word count.
*   Prints a cleaning log showing the raw and clean row counts and what was removed.

### 3. Data Visualisation and Exploration
*   Price distribution, price by rating (box plot and bar chart), and price versus stock quantity.
*   Books per rating and average price by stock level.
*   Genre comparisons, including a **permutation test** that checks whether the gap between the cheapest and most expensive genre is bigger than chance would produce. Catch-all labels on the site ("Default", "Add a comment") are left out of that comparison.
*   A correlation heatmap and the most frequent words in the descriptions.
*   Every plot is followed by a short interpretation printed from the actual results.

### 4. Predictive Modelling
*   Linear regression (scikit-learn) with an 80/20 train/test split (`random_state=42`).
*   Genre is converted with `pd.get_dummies()`. Genres with fewer than 10 books are grouped as "Other", and one genre is dropped as the reference category.
*   If a word-count column is almost identical to its length column (correlation above 0.9), the word-count column is dropped to avoid collinearity.
*   Three models are compared: a baseline (predict the mean), numeric features only, and numeric features plus genre.
*   Evaluated with R², RMSE, MAE and 5-fold cross-validation.

### 5. Reporting
*   The notebook generates a PDF report from its own results, so every number in the report matches the notebook.

---

## Key Results

| Finding | Result |
| :--- | :--- |
| Books scraped | 1,000 books across 50 genres, 0 failed pages |
| Price | £10.00 to £59.99, mean £35.07, median £35.98 (spread almost evenly across the range) |
| Rating vs price | Correlation +0.03: no meaningful relationship |
| Stock vs price | Correlation −0.01: no meaningful relationship |
| Genre gap | Travel (£39.79) vs Food and Drink (£31.41), a £8.38 gap; permutation test p = 0.976, so it is consistent with chance |

**Model results** (from `model_results.csv`):

| Model | Test R² | Test RMSE (£) | 5-fold CV R² |
| :--- | ---: | ---: | ---: |
| Baseline (predict the mean) | −0.0051 | 14.53 | −0.0030 |
| Linear regression: numeric only | −0.0179 | 14.62 | −0.0135 |
| Linear regression: numeric + genre | −0.0710 | 15.00 | −0.0675 |

The visible catalogue attributes do not predict price: neither linear regression beats the baseline of always guessing the average price.

---

## How to Run the Project

### Prerequisites
*   Python 3.9 or higher (Python 3.12 recommended).
*   VS Code with the **Python** and **Jupyter** extensions.
*   An internet connection (needed for scraping).

### Step-by-Step Setup
1. **Open the project folder in VS Code** (File > Open Folder).
2. **Install the packages** in the VS Code terminal:
   ```bash
   python -m pip install -r requirements.txt
   ```
3. **Open the notebook:** `BookAnalytics_Assignment/Book_Market_Analytics.ipynb`
4. **Select the kernel** (top right) and choose the same Python you installed the packages into.
5. **Run everything:** press `Ctrl+Shift+P`, type `restart kernel and run all`, and click **Jupyter: Restart Kernel and Run All Cells**.
6. **Wait for the scraping cell to finish.** Scraping all 1,000 book pages one at a time takes roughly 5 to 10 minutes on a fast connection, and longer on a slow one. The cell prints a progress line every 100 books. Do not interrupt it.

*(Note: the dataset and report are created when the notebook runs. The last cell checks that every output file exists. The saved notebook already contains the outputs from a full run, so it can be read without re-running the scrape.)*

---

## Project Structure

```text
BookAnalytics_Assignment/
│
├── Book_Market_Analytics.ipynb          # Main notebook (scraping, cleaning, EDA, model, report)
├── books_clean.csv                      # Final cleaned dataset (generated)
├── Book_Market_Analytics_Report.pdf     # Professional report (generated)
├── books_raw.csv                        # Raw scraped data (generated, supporting file)
└── model_results.csv                    # Model evaluation metrics (generated, supporting file)

requirements.txt                         # Python packages needed
README.md                                # This file
```

## Dataset Columns (`books_clean.csv`)

| Column | Description |
| :--- | :--- |
| `upc` | Unique product code |
| `title` | Book title |
| `genre` | Book genre (category) |
| `price` | Price in GBP (£) |
| `rating` | Star rating, 1 to 5 |
| `in_stock` | 1 if in stock, otherwise 0 (every book on this site is in stock, so it is not used in the model) |
| `stock_quantity` | Number of copies available |
| `num_reviews` | Number of reviews shown on the site (always 0 on this site, so it is not used in the model) |
| `title_length` | Characters in the title |
| `title_word_count` | Words in the title |
| `description` | Cleaned book description text (empty for the 2 books without one) |
| `description_length` | Characters in the description |
| `description_word_count` | Words in the description |
| `has_description` | 1 if the book has a description, otherwise 0 |
| `page` | Listing page the book was found on |

---

## Checklist for the Marker

1. **Scraping:** the scraping cell prints `DONE. Books scraped: 1000 | failed book pages: 0` and uses BeautifulSoup.
2. **Cleaning:** the cleaning section lists every decision and the reason for it, and the cleaning log shows the row counts before and after.
3. **Dataset:** `books_clean.csv` contains 1,000 rows and 15 columns.
4. **Visualisation:** each plot is followed by an interpretation written from the actual results.
5. **Modelling:** the results table shows the baseline and both linear regression models with test and cross-validated metrics.
6. **Report:** `Book_Market_Analytics_Report.pdf` includes the executive summary, methodology, key insights, modelling outcomes, limitations, recommendations and a conclusion.

> **Note:** Books to Scrape is a practice website, so its prices are not set by a real market. The results illustrate the method rather than the true economics of bookselling.