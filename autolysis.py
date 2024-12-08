# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",
#   "matplotlib",
#   "seaborn",
#   "httpx",
# ]
# ///

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import httpx

# Step 1: Load the CSV file
def load_csv(file_path):
    try:
        data = pd.read_csv(file_path,encoding='latin1')
        print(f"Successfully loaded {len(data)} rows and {len(data.columns)} columns from {file_path}.")
        return data
    except Exception as e:
        print(f"Error loading file: {e}")
        exit(1)

# Step 2: Perform a quick preview of the data
def preview_data(data):
    print("\nDataset Preview:")
    print(data.head())
    print("\nColumn Information:")
    print(data.info())
    print("\nSummary Statistics:")
    print(data.describe(include="all"))
# Step 3: Analyze missing values
def analyze_missing_values(data):
    missing = data.isnull().sum()
    print("\nMissing Values:")
    print(missing[missing > 0])

# Step 4: Compute basic summary statistics
def compute_statistics(data):
    print("\nSummary Statistics:")
    print(data.describe(include="all"))

# Step 5: Generate a correlation matrix (if numerical columns exist)
def analyze_correlation(data):
    numeric_data = data.select_dtypes(include=['number'])
    if numeric_data.empty:
        print("\nNo numerical columns found for correlation analysis.")
        return None
    correlation = numeric_data.corr()
    print("\nCorrelation Matrix:")
    print(correlation)
    return correlation
# Step 6: Visualize missing values as a heatmap
def visualize_missing_values(data, output_file="missing_values.png"):
    # plt.figure(figsize=(10, 6))
    plt.figure(figsize=(6.4, 6.4))
    sns.heatmap(data.isnull(), cbar=False, cmap="viridis")
    plt.title("Missing Values Heatmap")
    plt.savefig(output_file, dpi = 100)
    print(f"Saved missing values heatmap as {output_file}.")
    plt.close()

# Step 7: Visualize correlation matrix as a heatmap
def visualize_correlation(correlation, output_file="correlation_matrix.png"):
    if correlation is None:
        print("No numerical data for correlation matrix. Skipping visualization.")
        return
    plt.figure(figsize=(6.4, 6.4))
    sns.heatmap(correlation, annot=True, fmt=".2f", cmap="coolwarm")
    plt.title("Correlation Matrix")
    plt.savefig(output_file,dpi=100)
    print(f"Saved correlation matrix heatmap as {output_file}.")
    plt.close()


def query_llm(prompt):
    """
    Queries GPT-4o-Mini via AI Proxy with the given prompt.
    """
    AIPROXY_TOKEN = os.environ.get("AIPROXY_TOKEN")
    if not AIPROXY_TOKEN:
        print("AIPROXY_TOKEN is not set. Please set it before running the script.")
        exit(1)

    headers = {
        "Authorization": f"Bearer {AIPROXY_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant analyzing a dataset."},
            {"role": "user", "content": prompt},
        ],
    }

    try:
        response = httpx.post("https://aiproxy.sanand.workers.dev/openai/v1/chat/completions", headers=headers, json=data,timeout=60.0)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error querying LLM: {e}")
        return None

def generate_insights(data):
    # Summarize dataset structure
    dataset_summary = f"The dataset has {data.shape[0]} rows and {data.shape[1]} columns."
    column_info = "The columns are:\n" + "\n".join([f"- {col} ({dtype})" for col, dtype in zip(data.columns, data.dtypes)])
    missing_summary = f"There are {data.isnull().sum().sum()} missing values in the dataset."

    # Create the prompt for the LLM
    # prompt = (
    #     f"Here is the summary of a dataset:\n\n"
    #     f"{dataset_summary}\n\n"
    #     f"{column_info}\n\n"
    #     f"{missing_summary}\n\n"
    #     f"Based on this information, please provide insights about the dataset and "
    #     f"recommend possible analyses or actions to take."
    # )
    prompt = (
    f"Here is the summary of a dataset:\n\n"
    f"The dataset has {data.shape[0]} rows and {data.shape[1]} columns.\n"
    f"The columns are:\n" + "\n".join([f"- {col} ({dtype})" for col, dtype in zip(data.columns, data.dtypes)]) + "\n\n"
    f"There are {data.isnull().sum().sum()} missing values in the dataset.\n"
    f"The basic statistics of numerical columns are:\n{data.describe(include='number').to_string()}\n\n"
    f"Based on this information, please narrate a story about the dataset. Describe:\n"
    f"1. The data received.\n"
    f"2. The analyses carried out.\n"
    f"3. The insights discovered.\n"
    f"4. The implications of these findings (what actions to take).\n"
    f"Additionally, suggest any further analysis that could provide more insights."
        )


    # Query the LLM
    insights = query_llm(prompt)
    if insights:
        print("\nLLM Insights:")
        print(insights)
    return insights

def create_readme(data, insights, output_files):
    """
    Generate a Markdown report based on the analysis and LLM insights.
    Args:
        data (DataFrame): The dataset analyzed.
        insights (str): Insights generated by the LLM.
        output_files (list): List of image file names generated.
    """
    with open("README.md", "w") as readme:
        readme.write("# Dataset Analysis Report\n\n")
        readme.write("## Dataset Overview\n")
        readme.write(f"The dataset contains {data.shape[0]} rows and {data.shape[1]} columns.\n\n")
        readme.write("### Columns\n")
        for col, dtype in zip(data.columns, data.dtypes):
            readme.write(f"- **{col}**: {dtype}\n")
        readme.write("\n")

        readme.write("## Insights from Analysis\n")
        if insights:
            readme.write(insights + "\n\n")
        else:
            readme.write("No insights were generated.\n\n")

        readme.write("## Visualizations\n")
        for output_file in output_files:
            readme.write(f"![Visualization]({output_file})\n")

    print("README.md generated successfully.")


if __name__ == "__main__":
    # Expecting the file name as the first argument
    import sys
    if len(sys.argv) != 2:
        print("Usage: uv run autolysis.py <dataset.csv>")
        exit(1)

    # Load the dataset
    file_path = sys.argv[1]
    data = load_csv(file_path)

    # Preview the data
    preview_data(data)
    #Analyze missing values
    analyze_missing_values(data)

    # Compute summary statistics
    compute_statistics(data)

    # Analyze correlations
    correlation = analyze_correlation(data)
    # Visualize missing values
    visualize_missing_values(data)

    # Visualize correlation matrix
    visualize_correlation(correlation)
    
    # Generate insights using LLM
    insights = generate_insights(data)
    # Generate the report
    create_readme(
        data,
        insights,
        output_files=["missing_values.png", "correlation_matrix.png"]
    )