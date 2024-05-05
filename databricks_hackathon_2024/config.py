# Databricks notebook source
# MAGIC %md 
# MAGIC ## Configuration file
# MAGIC
# MAGIC Please change your catalog and schema here to run the demo on a different catalog.
# MAGIC
# MAGIC <!-- Collect usage data (view). Remove it to disable collection or disable tracker during installation. View README for more details.  -->
# MAGIC <img width="1px" src="https://ppxrzfxige.execute-api.us-west-2.amazonaws.com/v1/analytics?category=data-science&org_id=2747756931234785&notebook=%2Fconfig&demo_name=llm-rag-chatbot&event=VIEW&path=%2F_dbdemos%2Fdata-science%2Fllm-rag-chatbot%2Fconfig&version=1">

# COMMAND ----------

# to be configured
desired_chunk_size = 400
desired_overlap_size = 20
desired_k_value = 3
iterative_text = f"_chunk_{desired_chunk_size}_op_{desired_overlap_size}_k_{desired_k_value}" # _chunk_200_op_20_k_3

### vector index name
index_name = f"pdf_transformed_self_managed_vector_search_index{iterative_text}"
## chatbot model name
model_name = f"asset_nav_chatbot_model_version_chunk_{desired_chunk_size}"
## chatbot run_name_in_rag_evaluation_notebook
run_name_chatbot_creation = f'asset_nav_chatbot_model_chunk_{desired_chunk_size}'

## chatbot run_name_in_rag_evaluation_notebook
run_name_evaluation = f'asset_nav_chunk_{desired_chunk_size}'

# automated inference use case
catalog = "main"
VECTOR_SEARCH_ENDPOINT_NAME="asset_nav_vector_search_endpoint_chunk_fourhundred"
dbName = db = "asset_nav" + iterative_text
DATABRICKS_SITEMAP_URL = "https://docs.databricks.com/en/doc-sitemap.xml"

# COMMAND ----------

# MAGIC %md
# MAGIC ### License
# MAGIC This demo installs the following external libraries on top of DBR(ML):
# MAGIC
# MAGIC
# MAGIC | Library | License |
# MAGIC |---------|---------|
# MAGIC | langchain     | [MIT](https://github.com/langchain-ai/langchain/blob/master/LICENSE)     |
# MAGIC | lxml      | [BSD-3](https://pypi.org/project/lxml/)     |
# MAGIC | transformers      | [Apache 2.0](https://github.com/huggingface/transformers/blob/main/LICENSE)     |
# MAGIC | unstructured      | [Apache 2.0](https://github.com/Unstructured-IO/unstructured/blob/main/LICENSE.md)     |
# MAGIC | llama-index      | [MIT](https://github.com/run-llama/llama_index/blob/main/LICENSE)     |
# MAGIC | tesseract      | [Apache 2.0](https://github.com/tesseract-ocr/tesseract/blob/main/LICENSE)     |
# MAGIC | poppler-utils      | [MIT](https://github.com/skmetaly/poppler-utils/blob/master/LICENSE)     |
# MAGIC | textstat      | [MIT](https://pypi.org/project/textstat/)     |
# MAGIC | tiktoken      | [MIT](https://github.com/openai/tiktoken/blob/main/LICENSE)     |
# MAGIC | evaluate      | [Apache2](https://pypi.org/project/evaluate/)     |
# MAGIC | torch      | [BDS-3](https://github.com/intel/torch/blob/master/LICENSE.md)     |
# MAGIC | tiktoken      | [MIT](https://github.com/openai/tiktoken/blob/main/LICENSE)     |
# MAGIC
# MAGIC
# MAGIC
# MAGIC
