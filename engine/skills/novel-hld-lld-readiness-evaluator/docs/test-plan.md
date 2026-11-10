# Test plan

1. 正向：真实 coordinator 依次签发 consumer、fidelity、publisher；两次执行字节稳定，最终 HQ2 ready。
2. 隔离：consumer allowlist 不含 machine package/canonical/traceability；真实 OS workspace 读取不超出 work/gate/state 与 mode allowlist。
3. 校准：测试主动读取一个未授权 HP1 成员，读取审计必须捕获。
4. 篡改：越权加入呈现报告、handoff 修改后重封、伪造 sealed consumer、漏读/多读、伪 task id 均被拒绝或本地 revise。
5. 证明：删除 trace evidence 后即使结构仍合法，也因对象覆盖不完整而 revise。
6. 代数：upstream、author、reality 三种 origin 映射正确；任一内部任务非 ready 时 publisher 按 first-nonready 发布且无 completion。
7. 闭包：schema extra、重复、重排、逃逸、缺失、内容漂移均有负例。
