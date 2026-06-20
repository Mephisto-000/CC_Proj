# Git Workflow Rules

## Push Policy

- 禁止自行執行 git push
- 執行 git push 前必須先取得使用者明確同意

## Commit Convention

所有 commit 必須遵守 Conventional Commits：

允許的 type：

- feat
- fix
- docs
- style
- refactor
- perf
- test
- chore
- revert

規範：

- commit message 使用繁體中文
- 專有名詞保留英文
- subject 簡潔明確
- 不超過 50 字
- 不加句號
- scope 必須明確
- 大型修改需補充 body
- body 每行不超過 72 字

範例：

feat(auth): 新增 JWT refresh token 機制

fix(payment): 修正重複交易建立問題

refactor(ai-agent): 簡化 prompt pipeline 流程

perf(inference): 降低 embedding latency

docs(api): 更新 webhook 串接文件