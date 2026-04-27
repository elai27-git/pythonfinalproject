
# Import packages
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import datetime

# Heading
st.set_page_config(page_title="My Reading Dashboard", layout="wide")
st.title("📚 My Reading Dashboard")
st.subheader("Created by Emily Lai for Python for MBAs")

## Explanation of project
st.write("""Around June 2023, I decided to get back in reading, which was one of my favorite things to do as a kid.
I had grown to sort of dislike reading in high school due to some poor experiences in English classes, so I was determined to rediscover the joy of reading leisurely.
That year, I read 35 books by December 2023.

In January 2024, I made an ambitious New Year's Resolution to read 52 books that year, 1 per week.
I wanted a better way to track the books I was reading than the Notes app on my phone, so I decided to use Goodreads to track my progress and get recommendations for what to read next.
However, I really dislike the UI/UX of Goodreads."""
)
st.write("""Therefore, I wanted to use this project as an opportunity to build a personal reading dashboard that will do the following:

1. Provide key statistics, such as total books read, number of books read this month, whether I'm on track to hit my goal, average rating, and so on.

2. Use AI to generate recommendations for the next book to read.

3. Track the books I've read, including the 1-2 sentence reviews I've written on my Notes app in my phone, as well as the books I want to read."""
)

# Set up dataframes
## Load Goodreads data as a dataframe
df_goodreads = pd.read_csv("goodreads_library_export.csv")

## Update column names to replace spaces with _
df_goodreads.columns = df_goodreads.columns.str.replace(' ', '_')

## Clean ISBN and ISBN13 columns
df_goodreads['ISBN'] = df_goodreads['ISBN'].str.replace('="', '', regex=True).str.replace('"', '', regex=True)
df_goodreads['ISBN13'] = df_goodreads['ISBN13'].str.replace('="', '', regex=True).str.replace('"', '', regex=True)

## Update data types for Date columns
df_goodreads['Date_Added'] = pd.to_datetime(df_goodreads['Date_Added'])
df_goodreads['Date_Read'] = pd.to_datetime(df_goodreads['Date_Read'])
# Assuming Original_Publication_Year and Year_Published are just years (e.g., 2005)
# Convert them to numeric and then to nullable integer type to retain year as a number
df_goodreads['Original_Publication_Year'] = pd.to_numeric(df_goodreads['Original_Publication_Year'], errors='coerce').astype('Int64')
df_goodreads['Year_Published'] = pd.to_numeric(df_goodreads['Year_Published'], errors='coerce').astype('Int64')

## Update data types for My_Review, Spoiler, and Private_Notes
df_goodreads['My_Review'] = df_goodreads['My_Review'].astype(str)
df_goodreads['Spoiler'] = df_goodreads['Spoiler'].astype(str)
df_goodreads['Private_Notes'] = df_goodreads['Private_Notes'].astype(str)

## Load my reviews as a dataframe
df_my_reviews = pd.read_csv("my_reviews.csv")

# Variables and Calculations
# Filter df_goodreads to get only 'read' books for df_read first
df_read = df_goodreads[df_goodreads.Exclusive_Shelf == "read"].copy() # .copy() to avoid SettingWithCopyWarning

#Filter df_goodreads to get only 'to-read' books for df_to_read
df_to_read = df_goodreads[df_goodreads.Exclusive_Shelf == "to-read"].copy() # .copy() to avoid SettingWithCopyWarning

# Merge df_read with df_my_reviews to incorporate personal reviews
df_read = pd.merge(
    df_read,
    df_my_reviews[['Title', 'Author', 'My_Review']].rename(columns={'My_Review': 'My_Review_personal'}), # Rename to clearly indicate personal review
    on=['Title', 'Author'],
    how='left'
)

# Prioritize personal reviews: fill df_read['My_Review'] with 'My_Review_personal' where available.
# The original 'My_Review' in df_read (from df_goodreads) will be used if 'My_Review_personal' is NaN.
df_read['My_Review'] = df_read['My_Review_personal'].fillna(df_read['My_Review'])

# Drop the temporary 'My_Review_personal' column
df_read = df_read.drop(columns=['My_Review_personal'])

total_books_read_alltime = df_read.shape[0]

current_year = pd.Timestamp.now().year
current_month = pd.Timestamp.now().month

# Calculate previous month and year for comparisons
if current_month == 1:
    # If current month is January, previous month is December of the previous year
    previous_month_comp = 12
    previous_month_year_comp = current_year - 1
else:
    # Otherwise, previous month is current month - 1 in the current year
    previous_month_comp = current_month - 1
    previous_month_year_comp = current_year

total_books_read_current_yr = df_read[df_read.Date_Read.dt.year == current_year].shape[0]

total_books_read_previous_yr = df_read[(df_read.Date_Read.dt.year == current_year - 1) &
                                         (df_read.Date_Read.dt.month <= current_month)].shape[0]

total_books_read_current_month = df_read[(df_read.Date_Read.dt.year == current_year) &
                                         (df_read.Date_Read.dt.month == current_month)].shape[0]

total_books_read_previous_month = df_read[(df_read.Date_Read.dt.year == previous_month_year_comp) &
                                          (df_read.Date_Read.dt.month == previous_month_comp)].shape[0]

total_pages_read_alltime = df_read['Number_of_Pages'].sum()

total_pages_read_current_yr = df_read[df_read.Date_Read.dt.year == current_year]['Number_of_Pages'].sum()

total_pages_read_previous_yr = df_read[(df_read.Date_Read.dt.year == current_year - 1) &
                                         (df_read.Date_Read.dt.month <= current_month)]['Number_of_Pages'].sum()

total_pages_read_current_month = df_read[(df_read.Date_Read.dt.year == current_year) &
                                         (df_read.Date_Read.dt.month == current_month)]['Number_of_Pages'].sum()

total_pages_read_previous_month = df_read[(df_read.Date_Read.dt.year == previous_month_year_comp) &
                                          (df_read.Date_Read.dt.month == previous_month_comp)]['Number_of_Pages'].sum()

# Calculate deltas for metrics
delta_books_year = int(total_books_read_current_yr - total_books_read_previous_yr)
delta_books_month = int(total_books_read_current_month - total_books_read_previous_month)
delta_pages_year = int(total_pages_read_current_yr - total_pages_read_previous_yr)
delta_pages_month = int(total_pages_read_current_month - total_pages_read_previous_month)

# --- Average Rating Calculations ---
df_read_with_rating = df_read[df_read['My_Rating'].notna() & (df_read['My_Rating'] > 0)]

average_rating_alltime = df_read_with_rating['My_Rating'].mean()
average_rating_current_yr = df_read_with_rating[df_read_with_rating.Date_Read.dt.year == current_year]['My_Rating'].mean()
average_rating_previous_yr = df_read_with_rating[(df_read_with_rating.Date_Read.dt.year == current_year - 1) &
                                                  (df_read_with_rating.Date_Read.dt.month <= current_month)]['My_Rating'].mean()
average_rating_current_month = df_read_with_rating[(df_read_with_rating.Date_Read.dt.year == current_year) &
                                                  (df_read_with_rating.Date_Read.dt.month == current_month)]['My_Rating'].mean()
average_rating_previous_month = df_read_with_rating[(df_read_with_rating.Date_Read.dt.year == previous_month_year_comp) &
                                                   (df_read_with_rating.Date_Read.dt.month == previous_month_comp)]['My_Rating'].mean()

# Handle potential NaN values for averages if no books are read in a period
average_rating_alltime = round(average_rating_alltime, 2) if pd.notna(average_rating_alltime) else 0.0
average_rating_current_yr = round(average_rating_current_yr, 2) if pd.notna(average_rating_current_yr) else 0.0
average_rating_previous_yr = round(average_rating_previous_yr, 2) if pd.notna(average_rating_previous_yr) else 0.0
average_rating_current_month = round(average_rating_current_month, 2) if pd.notna(average_rating_current_month) else 0.0
average_rating_previous_month = round(average_rating_previous_month, 2) if pd.notna(average_rating_previous_month) else 0.0

# Calculate deltas for average ratings
delta_avg_rating_year = round(average_rating_current_yr - average_rating_previous_yr, 2) if (average_rating_previous_yr != 0) else 0.0
delta_avg_rating_month = round(average_rating_current_month - average_rating_previous_month, 2) if (average_rating_previous_month != 0) else 0.0

# Create tabs for each section
tab1, tab2, tab3 = st.tabs(["📊 Key Statistics", "📢 Recommendations", "🗒 List of Books"])

# Key Statistics tab
with tab1:
  ## Progress to Goal
  reading_goals = {
      2023: 35,
      2024: 52,
      2025: 26,
      2026: 26
  }

  st.subheader("Progress to Goal")

  # Get available years from data read and years with goals
  available_years = sorted(df_read['Date_Read'].dt.year.dropna().astype(int).unique(), reverse=True)
  # Combine years from data and years with goals, ensuring current_year is included if it has a goal
  all_relevant_years = sorted(list(set(available_years).union(set(reading_goals.keys()))), reverse=True)

  # Filter for years with goals that are not in the future
  years_for_selection = [y for y in all_relevant_years if y <= current_year]

  if not years_for_selection:
      st.info("No reading goals defined or relevant years with data to display progress.")
  else:
      # Set default selection to current year if available, otherwise the most recent year with a goal
      default_index = 0
      if current_year in years_for_selection:
          default_index = years_for_selection.index(current_year)
      elif current_year + 1 in years_for_selection: # If next year is present, make it default if current year is not.
          default_index = years_for_selection.index(current_year+1)

      selected_goal_year = st.selectbox('Select Year for Goal Progress', years_for_selection, index=default_index)

      goal = reading_goals.get(selected_goal_year)

      if goal is not None:
          books_read_in_year = df_read[df_read.Date_Read.dt.year == selected_goal_year].shape[0]

          st.write(f"**Goal for {selected_goal_year}:** {goal} books")
          st.write(f"**Books Read in {selected_goal_year}:** {books_read_in_year}")

          progress_percentage = (books_read_in_year / goal) * 100 if goal > 0 else 0

          if selected_goal_year < current_year:
              # Past year
              if books_read_in_year >= goal:
                  st.success(f"🥳 Goal of {goal} books reached in {selected_goal_year}!")
              else:
                  st.error(f"😔 Goal of {goal} books not reached in {selected_goal_year}. {goal - books_read_in_year} books short.")
              st.progress(min(int(progress_percentage), 100))

          elif selected_goal_year == current_year:
              # Current year
              today = datetime.date.today()
              current_week_of_year = today.isocalendar()[1]
              # Assuming an even distribution of reading throughout the year for tracking
              expected_books_on_track = (goal / 52) * current_week_of_year

              st.write(f"**Current Week:** {current_week_of_year} of 52")
              st.write(f"**Expected Books by now:** {expected_books_on_track:.1f}")

              if books_read_in_year >= goal:
                  st.success(f"🥳 Already reached goal of {goal} books in {selected_goal_year}!")
              elif books_read_in_year >= expected_books_on_track:
                  st.info(f"✅ On track to reach goal of {goal} books in {selected_goal_year}!")
              else:
                  st.warning(f"⚠️ Behind schedule for goal of {goal} books in {selected_goal_year}. Need to read {expected_books_on_track - books_read_in_year:.1f} more to be on track.")
              st.progress(min(int(progress_percentage), 100))
          else: # Future year (though filtered out by years_for_selection)
              st.info(f"Goal for {selected_goal_year} is {goal} books.")
      else:
          st.info(f"No reading goal defined for {selected_goal_year}.")

  ## Display Metrics - Books
  st.subheader("Reading Stats")
  col1, col2, col3 = st.columns(3)
  with col1:
    st.metric(f"Total Books Read All Time", total_books_read_alltime)
  with col2:
    if delta_books_year == 0:
      st.metric("Total Books Read This Year", total_books_read_current_yr)
    else:
      st.metric("Total Books Read This Year", total_books_read_current_yr, delta=delta_books_year)
    st.caption("vs. same period last year")
  with col3:
    if delta_books_month == 0:
      st.metric("Total Books Read This Month", total_books_read_current_month)
    else:
      st.metric("Total Books Read This Month", total_books_read_current_month, delta=delta_books_month)
    st.caption("vs. previous month")

  ## Display Metrics - Pages
  col1, col2, col3 = st.columns(3)
  with col1:
    st.metric("Total Pages Read All Time", total_pages_read_alltime)
  with col2:
    if delta_pages_year == 0:
      st.metric("Total Pages Read This Year", total_pages_read_current_yr)
    else:
      st.metric("Total Pages Read This Year", total_pages_read_current_yr, delta=delta_pages_year)
    st.caption("vs. same period last year")
  with col3:
    if delta_pages_month == 0:
      st.metric("Total Pages Read This Month", total_pages_read_current_month)
    else:
      st.metric("Total Pages Read This Month", total_pages_read_current_month, delta=delta_pages_month)
    st.caption("vs. previous month")

  # --- Average Rating Analysis ---
  st.subheader("Average Rating Analysis")
  col1, col2, col3 = st.columns(3)
  with col1:
    st.metric("Overall Average Rating", average_rating_alltime)
  with col2:
    if delta_avg_rating_year == 0.0:
      st.metric("Average Rating This Year", average_rating_current_yr)
    else:
      st.metric("Average Rating This Year", average_rating_current_yr, delta=delta_avg_rating_year)
    st.caption("vs. same period last year")
  with col3:
    if delta_avg_rating_month == 0.0:
      st.metric("Average Rating This Month", average_rating_current_month)
    else:
      st.metric("Average Rating This Month", average_rating_current_month, delta=delta_avg_rating_month)
    st.caption("vs. previous month")

  ## Monthly Reading Trend Graph
  st.subheader("Monthly Reading Trend")

  ## Get all unique years from the data, excluding NaT values
  available_years = sorted(df_read['Date_Read'].dt.year.dropna().astype(int).unique(), reverse=True)

  ## Default to current and previous year if available, otherwise pick first two available
  default_year1 = pd.Timestamp.now().year if pd.Timestamp.now().year in available_years else (available_years[0] if available_years else None)
  default_year2 = pd.Timestamp.now().year - 1 if (pd.Timestamp.now().year - 1) in available_years else (available_years[1] if len(available_years) > 1 else None)

  col_select_year1, col_select_year2 = st.columns(2)
  with col_select_year1:
    selected_year1 = st.selectbox('Select First Year', available_years, index=available_years.index(default_year1) if default_year1 in available_years else 0)
  with col_select_year2:
    selected_year2 = st.selectbox('Select Second Year', available_years, index=available_years.index(default_year2) if default_year2 in available_years else (1 if len(available_years) > 1 else 0))

  current_year = pd.Timestamp.now().year
  current_month_num = pd.Timestamp.now().month

  df_read['Year'] = df_read['Date_Read'].dt.year
  df_read['Month_num'] = df_read['Date_Read'].dt.month # Add Month_num for filtering
  df_read['Month'] = df_read['Date_Read'].dt.month_name()

  ordered_month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

  def get_monthly_counts(df, year, current_year, current_month_num, ordered_month_names):
      year_data = df[df['Year'] == year].copy()
      months_for_reindex = ordered_month_names

      if year == current_year:
          year_data = year_data[year_data['Month_num'] <= current_month_num]
          months_for_reindex = ordered_month_names[:current_month_num]

      monthly_counts = year_data.groupby('Month').size().reindex(months_for_reindex, fill_value=0)
      return monthly_counts

  monthly_counts_year1 = get_monthly_counts(df_read, selected_year1, current_year, current_month_num, ordered_month_names)
  monthly_counts_year2 = get_monthly_counts(df_read, selected_year2, current_year, current_month_num, ordered_month_names)

  ## Create dataframes for plotting
  df_plot_year1 = pd.DataFrame({
      'Month': monthly_counts_year1.index,
      'Books_Read': monthly_counts_year1.values,
      'Year': str(int(selected_year1)) # Convert to string for hue in sns.lineplot
  })

  df_plot_year2 = pd.DataFrame({
      'Month': monthly_counts_year2.index,
      'Books_Read': monthly_counts_year2.values,
      'Year': str(int(selected_year2)) # Convert to string for hue in sns.lineplot
  })

  plot_data_final = pd.concat([df_plot_year1, df_plot_year2])
  plot_data_final['Month'] = pd.Categorical(plot_data_final['Month'], categories=ordered_month_names, ordered=True)
  plot_data_final = plot_data_final.sort_values(['Year', 'Month'])

  plt.rcParams.update({'font.size': 8})
  fig, ax = plt.subplots(figsize=(4, 4))
  sns.lineplot(x='Month', y='Books_Read', hue='Year', data=plot_data_final, marker='o', ax=ax)
  ax.set_title(f'Number of Books Read Per Month ({int(selected_year1)} vs {int(selected_year2)})')
  ax.set_xlabel('Month')
  ax.set_ylabel('Number of Books')
  plt.xticks(rotation=45, ha='right')
  plt.tight_layout()
  st.pyplot(fig)


# Recommendations tab
with tab2:
    st.subheader("Books I Want to Read")
    st.write("The recommendations tab is still under development. Please check back later!")

# List of Books tab
with tab3:
  st.subheader("Books I've Read")
  ## Define columns to display
  display_columns = [
      'Title', 'My_Review', 'Author', 'ISBN', 'ISBN13', 'My_Rating', 'Publisher',
      'Number_of_Pages', 'Year_Published', 'Date_Read'
  ]

  ## Create a copy of df_read with only relevant rows and columns
  df_list = df_read[display_columns].copy()

  ## Format 'Year_Published' and 'Date_Read' for display
  df_list['Year_Published'] = df_list['Year_Published'].fillna('').astype(str)
  df_list['Date_Read'] = df_list['Date_Read'].dt.strftime('%Y-%m-%d').fillna('')

  # Sort by 'Date_Read' in descending order
  df_list = df_list.sort_values(by='Date_Read', ascending=False)

  ## Function to get book cover URL from Open Library API
  @st.cache_data
  def get_book_cover_url(isbn=None, isbn13=None):
      # Open Library cover API: https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg
      if isbn and str(isbn).strip() != '': # Convert to string and check if not empty
          return f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
      elif isbn13 and str(isbn13).strip() != '': # Convert to string and check if not empty
          return f"https://covers.openlibrary.org/b/isbn/{isbn13}-M.jpg"
      return None

  ## Add a column for book cover URLs
  df_list['Cover'] = None

  with st.spinner("Fetching book cover images (this might take a moment)..."):
      for index, row in df_list.iterrows():
          isbn = row['ISBN']
          isbn13 = row['ISBN13']
          cover_url = get_book_cover_url(isbn, isbn13)
          if cover_url:
              df_list.at[index, 'Cover'] = cover_url # Assign URL directly
          else:
              df_list.at[index, 'Cover'] = ""

  ## Add 'Cover' to the display columns, placing it at the beginning
  display_columns_with_cover = ['Cover'] + display_columns

  ## Display the DataFrame using st.dataframe with ImageColumn for covers
  st.dataframe(df_list[display_columns_with_cover],
               column_config={
                   "Cover": st.column_config.ImageColumn("Book_Cover", width="small")
               },
               hide_index=True)

  st.subheader("Books I Want to Read")
  ## Define columns to display for to-read list
  display_columns_to_read = [
      'Title', 'Author', 'ISBN', 'ISBN13', 'Publisher',
      'Number_of_Pages', 'Year_Published','Date_Added'
  ]

  ## Create a copy of df_to_read with only relevant rows and columns
  df_list_to_read = df_to_read[display_columns_to_read].copy()

  ## Format 'Year_Published' for display
  df_list_to_read['Year_Published'] = df_list_to_read['Year_Published'].fillna('').astype(str)
  df_list_to_read['Date_Added'] = df_list_to_read['Date_Added'].dt.strftime('%Y-%m-%d').fillna('')

  # Sort by 'Date_Added' in descending order for to-read list
  df_list_to_read = df_list_to_read.sort_values(by='Date_Added', ascending=False)

  ## Add a column for book cover URLs
  df_list_to_read['Cover'] = None

  with st.spinner("Fetching book cover images for to-read list (this might take a moment)..."):
      for index, row in df_list_to_read.iterrows():
          isbn = row['ISBN']
          isbn13 = row['ISBN13']
          cover_url = get_book_cover_url(isbn, isbn13)
          if cover_url:
              df_list_to_read.at[index, 'Cover'] = cover_url # Assign URL directly
          else:
              df_list_to_read.at[index, 'Cover'] = ""

  ## Add 'Cover' to the display columns, placing it at the beginning
  display_columns_with_cover_to_read = ['Cover'] + display_columns_to_read

  ## Display the DataFrame using st.dataframe with ImageColumn for covers
  st.dataframe(df_list_to_read[display_columns_with_cover_to_read],
                 column_config={
                     "Cover": st.column_config.ImageColumn("Book_Cover", width="small")
                 },
                 hide_index=True)
