from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

# 替换为你的 client_secret.json 本地路径
CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_PICKLE = "token.pickle"

# 本地授权（会自动打开浏览器）
flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
# 本地浏览器授权，获取包含 refresh token 的凭证
credentials = flow.run_local_server(port=0)

# 保存凭证到文件
with open(TOKEN_PICKLE, "wb") as f:
    pickle.dump(credentials, f)
print("凭证已生成：token.pickle")