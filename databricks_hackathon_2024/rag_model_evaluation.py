# Databricks notebook source
# MAGIC %md
# MAGIC #Install libraries and modules

# COMMAND ----------

# MAGIC %pip install -q databricks-sdk==0.12.0 mlflow==2.10.1 textstat==0.7.3 tiktoken==0.5.1 evaluate==0.4.1 langchain==0.1.5 databricks-vectorsearch==0.22 transformers==4.30.2 torch==2.0.1 cloudpickle==2.2.1 pydantic==2.5.2 lxml==4.9.3
# MAGIC
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %run /Workspace/Repos/jingwen_huang@transalta.com/LLM_datathon_2024/databricks_hackathon_2024/_resources/00-init-advanced $reset_all_data=false

# COMMAND ----------

# MAGIC %md
# MAGIC #Import libaries and modules

# COMMAND ----------

from pyspark.sql.functions import col
import mlflow
from mlflow.deployments import get_deploy_client
from mlflow.metrics.genai.metric_definitions import answer_correctness, answer_relevance, faithfulness
from mlflow.metrics.genai import make_genai_metric, EvaluationExample
from mlflow.deployments import set_deployments_target
import plotly.express as px

# COMMAND ----------

# MAGIC %md
# MAGIC #Creating DBRX instruct as the judge for evaluation

# COMMAND ----------

deploy_client = get_deploy_client("databricks")

endpoint_name = "databricks-dbrx-instruct"

# #Let's query our external model endpoint
# answer_test = deploy_client.predict(endpoint=endpoint_name, inputs={"messages": [{"role": "user", "content": "What is Apache Spark?"}]})
# answer_test['choices'][0]['message']['content']

# COMMAND ----------

# MAGIC %md
# MAGIC #RAG model evaluation

# COMMAND ----------

# # %sql
# # DROP TABLE main.asset_nav.pdf_evaluation_clean

# drop_pdf_evaluation_clean_table_query = f"DROP TABLE {catalog}.{db}.pdf_evaluation_clean"
# spark.sql(drop_pdf_evaluation_clean_table_query)

# COMMAND ----------

# dbutils.fs.rm(f"dbfs:/Volumes/{catalog}/{db}/volume_oem_documentation/checkpoints/pdf_evaluation_clean_chunk", True)

# COMMAND ----------

# %sql
# --Note that we need to enable Change Data Feed on the table to create the index
# CREATE TABLE IF NOT EXISTS main.asset_nav.pdf_evaluation_clean (
#   id BIGINT GENERATED BY DEFAULT AS IDENTITY,
#   question STRING,
#   expected_answer STRING,
#   predicted_answer STRING
# ) TBLPROPERTIES (delta.enableChangeDataFeed = true);

create_pdf_evaluation_clean_table_query = f'''
                                            CREATE TABLE IF NOT EXISTS {catalog}.{db}.pdf_evaluation_clean (
                                              id BIGINT GENERATED BY DEFAULT AS IDENTITY,
                                              question STRING,
                                              expected_answer STRING,
                                              predicted_answer STRING
                                            ) TBLPROPERTIES (delta.enableChangeDataFeed = true);
                                    '''                          
spark.sql(create_pdf_evaluation_clean_table_query)

# COMMAND ----------

evaluation_dataset_path = "/Volumes/main/asset_nav/volume_oem_documentation/evaluation_data/solar_rag_pipeline_evaluation_datatset_manual_with_context.csv" # constant data source to load data from
df = spark.read.format("csv").option("header", "true").option("inferSchema", "true").load(evaluation_dataset_path)
df = df.withColumn("id", col("id").cast("bigint"))
display(df)

df.write.format("delta").mode("overwrite").option("mergeSchema", "true").saveAsTable(f"{catalog}.{db}.pdf_evaluation_clean")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Automated Evaluation of our chatbot model registered in Unity Catalog
# MAGIC
# MAGIC Retrieving the chatbot model we registered in Unity Catalog and predict answers for each questions in the evaluation set.

# COMMAND ----------

os.environ['DATABRICKS_TOKEN'] = dbutils.secrets.get("dbdemos", "rag_sp_token")
model_name = f"{catalog}.{db}.{model_name}"
model_version_to_evaluate = get_latest_model_version(model_name)
mlflow.set_registry_uri("databricks-uc")
rag_model = mlflow.langchain.load_model(f"models:/{model_name}/{model_version_to_evaluate}")

@pandas_udf("string")
def predict_answer(questions):
    def answer_question(question):
        dialog = {"messages": [{"role": "user", "content": question}]}
        return rag_model.invoke(dialog)['result']
    return questions.apply(answer_question)

# COMMAND ----------

df_qa = (spark.read.table(f'{catalog}.{db}.pdf_evaluation_clean')
                  .selectExpr('question as inputs', 'expected_answer as targets', 'context')
                  .where("targets is not null")
                  # .sample(fraction=0.005, seed=40) # .sample(fraction=0.005, seed=40): This line takes a random sample from the DataFrame. It randomly selects a fraction (0.5%) of the rows for the sample. The seed=40 parameter ensures that the sample is reproducible by setting a specific seed value.
        ) #small sample for interactive demo: This comment indicates that the sample size chosen (0.5%) is small for the purpose of an interactive demonstration.

df_qa_with_preds = df_qa.withColumn('preds', predict_answer(col('inputs'))).cache()
display(df_qa_with_preds)

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ##Automated LLM evaluation using DBRX as judge
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### Evaluation metrics to be used and the meaning for the metrics
# MAGIC
# MAGIC 1. answer_correctness
# MAGIC
# MAGIC   This function will create a genai metric used to evaluate the answer correctness of an LLM using the model provided. Answer correctness will be assessed by the accuracy of the provided output based on the ground_truth, which should be specified in the targets column.
# MAGIC
# MAGIC   The targets eval_arg must be provided as part of the input dataset or output predictions. This can be mapped to a column of a different name using col_mapping in the evaluator_config parameter, or using the targets parameter in mlflow.evaluate().
# MAGIC
# MAGIC
# MAGIC 2. answer_relevance
# MAGIC
# MAGIC   This function will create a genai metric used to evaluate the answer relevance of an LLM using the model provided. Answer relevance will be assessed based on the appropriateness and applicability of the output with respect to the input.
# MAGIC   
# MAGIC
# MAGIC 3. faithfulness
# MAGIC
# MAGIC   This function will create a genai metric used to evaluate the faithfullness of an LLM using the model provided. Faithfulness will be assessed based on how factually consistent the output is to the context.
# MAGIC
# MAGIC   The context eval_arg must be provided as part of the input dataset or output predictions. This can be mapped to a column of a different name using col_mapping in the evaluator_config parameter.

# COMMAND ----------


# Because we have our labels (answers) within the evaluation dataset, we can evaluate the answer correctness as part of our metric. Again, this is optional.
answer_correctness_metrics = answer_correctness(model=f"endpoints:/{endpoint_name}")
answer_relevance_metrics = answer_relevance(model=f"endpoints:/{endpoint_name}")
faithfulness_metrics = faithfulness(model=f"endpoints:/{endpoint_name}")
print(answer_correctness_metrics)

# COMMAND ----------

# MAGIC %md
# MAGIC ##Metrics templates
# MAGIC
# MAGIC Creating professionalism template

# COMMAND ----------

professionalism_example = EvaluationExample(
    input="What is an Inverter?",
    output=(
        # "MLflow is like your friendly neighborhood toolkit for managing your machine learning projects. It helps "
        # "you track experiments, package your code and models, and collaborate with your team, making the whole ML "
        # "workflow smoother. It's like your Swiss Army knife for machine learning!"
        ''' 
            Oh, dude, so, like, an inverter is this super cool thing in solar energy setups! It's basically this device that takes the direct current (DC) electricity generated by solar panels and flips it into alternating current (AC), which is what we use in our homes and stuff, you know? It's like the middleman between your solar panels and your appliances, making sure everything runs smoothly and you can use all that awesome solar power to run your gadgets and keep the lights on!
        '''
    ),
    score=2,
    justification=(
        "The response is written in a casual tone. It uses contractions, filler words such as 'like', and "
        "exclamation points, which make it sound less professional. "
    )
)

professionalism = make_genai_metric(
    name="professionalism",
    definition=(
        "Professionalism refers to the use of a formal, respectful, and appropriate style of communication that is "
        "tailored to the context and audience. It often involves avoiding overly casual language, slang, or "
        "colloquialisms, and instead using clear, concise, and respectful language."
    ),
    grading_prompt=(
        "Professionalism: If the answer is written using a professional tone, below are the details for different scores: "
        "- Score 1: Language is extremely casual, informal, and may include slang or colloquialisms. Not suitable for "
        "professional contexts."
        "- Score 2: Language is casual but generally respectful and avoids strong informality or slang. Acceptable in "
        "some informal professional settings."
        "- Score 3: Language is overall formal but still have casual words/phrases. Borderline for professional contexts."
        "- Score 4: Language is balanced and avoids extreme informality or formality. Suitable for most professional contexts. "
        "- Score 5: Language is noticeably formal, respectful, and avoids casual elements. Appropriate for formal "
        "business or academic settings. "
    ),
    model=f"endpoints:/{endpoint_name}",
    parameters={"temperature": 0.0},
    aggregations=["mean", "variance"],
    examples=[professionalism_example],
    greater_is_better=True
)

print(professionalism)

# COMMAND ----------

set_deployments_target("databricks")

#This will automatically log all
with mlflow.start_run(run_name="asset_nav") as run:
    eval_results = mlflow.evaluate(data = df_qa_with_preds.toPandas(), # evaluation data,
                                   model_type="question-answering", # toxicity and token_count will be evaluated   
                                   predictions="preds", # prediction column_name from eval_df
                                   targets = "targets",
                                   extra_metrics=[answer_correctness_metrics, answer_relevance_metrics, faithfulness_metrics, professionalism])
    
eval_results.metrics

# COMMAND ----------

df_genai_metrics = eval_results.tables["eval_results_table"]
display(df_genai_metrics)

# COMMAND ----------

px.histogram(df_genai_metrics, x="token_count", labels={"token_count": "Token Count"}, title="Distribution of Token Counts in Model Responses")

# COMMAND ----------

# Counting the occurrences of each answer correctness score
px.bar(df_genai_metrics['answer_correctness/v1/score'].value_counts(), title='Answer Correctness Score Distribution')

# COMMAND ----------

df_genai_metrics['toxicity'] = df_genai_metrics['toxicity/v1/score'] * 100
fig = px.scatter(df_genai_metrics, x='toxicity', y='answer_correctness/v1/score', title='Toxicity vs Correctness', size=[10]*len(df_genai_metrics))
fig.update_xaxes(tickformat=".2f")

# COMMAND ----------

# MAGIC %md
# MAGIC #Model is PRD ready

# COMMAND ----------

client = MlflowClient()
client.set_registered_model_alias(name=model_name, alias=f"{catalog}_{db}_prod", version=model_version_to_evaluate)
