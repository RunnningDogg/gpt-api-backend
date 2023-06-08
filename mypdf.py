from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import PyMuPDFLoader
import os


def createPDFIndex(username, filename):
    """给pdf文件创建索引
    Args:
        username (_type_): _description_
        filename (_type_): _description_
    """
    # loader = TextLoader('./union.txt', encoding='utf8')
    print(os.getcwd())
    loader = PyMuPDFLoader('./files/'+filename)

    # 1. load document
    documents = loader.load()
    # 2. 分词 text_splitter
    text_splitter = CharacterTextSplitter(
        chunk_size=600, chunk_overlap=0, separator='\n')

    # 2023年05月27日 补充 按照实际的chunk_size去设置maxmimum page_content
    new_documents = []
    for i in range(len(documents)):
        new_content = text_splitter.split_text(documents[i].page_content)
        for j in range(len(new_content)):
            document = documents[0].copy()
            document.page_content = new_content[j]
            document.metadata = documents[i].metadata
            new_documents.append(document)

    # 3. 指明embedding
    embeddings = OpenAIEmbeddings()
    # 4. 向量数据库引入数据
    directory_name = 'db/'+username+"_"+filename
    print("directory_name"+directory_name)
    db = Chroma.from_documents(
        new_documents, embeddings, persist_directory=directory_name)
    db.persist()
    print("persist database")


def search(query, filename, username):
    embedding = OpenAIEmbeddings()
    directory_name = 'db/'+username+"_"+filename
    vectordb = Chroma(persist_directory=directory_name,
                      embedding_function=embedding)
    docs = vectordb.similarity_search(query, k=4)
    return docs


def gen_prompt(docs, query) -> str:
    # To answer the question please only use the Context given, nothing else.Do not make up answer, simply say 'I don't know' if you are not sure.
    return f"""请你根据提供的上下文来回答问题,请不要自己编造答案.如果你不知道答案的话，请你说不知道。 
            问题: {query}
            上下文: {[doc.page_content for doc in docs]}
            答案:
            """


def prompt(query, docs):
    prompt = gen_prompt(docs, query)
    return prompt


if __name__ == "__main__":
    createPDFIndex("tony", "union")
