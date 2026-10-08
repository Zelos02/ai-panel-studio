# E2E tests

Playwright 场景位于 `frontend/e2e/panel.spec.ts`。测试会自动启动前后端，使用 deterministic Fake Provider 和 `.tmp` 下的 SQLite，不访问真实模型服务。

运行方式：

```powershell
cd frontend
npm run test:e2e
```
