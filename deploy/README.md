# MedFlow 生产部署指南

服务器：107.172.243.182（Ubuntu）｜域名均走 Cloudflare 代理（小黄云开启）｜后端端口 8000

架构：
```
浏览器 ── HTTPS ──> Cloudflare ── HTTPS ──> nginx(443) ──┬─ 静态文件 /var/www/medflow/{admin,doctor,patient}
                                                          ├─ /api/v1 ──> 127.0.0.1:8000 (uvicorn)
                                                          └─ /uploads ──> 127.0.0.1:8000
```

## 一、构建前端（本地开发机）

```bash
cd MedFlow-frontend
pnpm install
pnpm build:admin   # 产物 packages/admin/dist
pnpm build:doctor  # 产物 packages/doctor/dist
pnpm build:patient # 产物 packages/patient/dist
```

构建时自动加载各包的 `.env.production`（`VITE_API_BASE_URL=/api/v1`，相对路径同源调用）。
本地开发仍用 `.env`（localhost:8001），互不影响。

## 二、上传到服务器

```bash
scp -r packages/admin/dist   root@107.172.243.182:/var/www/medflow/admin
scp -r packages/doctor/dist  root@107.172.243.182:/var/www/medflow/doctor
scp -r packages/patient/dist root@107.172.243.182:/var/www/medflow/patient
```

## 三、服务器环境

```bash
apt install nginx
# 前端代码 + 后端代码放哪自己定，本文按 /srv/medflow 示例
mkdir -p /srv/medflow /var/www/medflow /etc/ssl/medflow
```

后端已按原方式运行在 8000 端口（见 `medflow-backend.service`，建议服务化后删掉手动进程）。

## 四、创建证书（你自己操作）

证书路径约定为 `/etc/ssl/medflow/origin.pem` + `/etc/ssl/medflow/origin.key`（nginx 模板里已写死，把证书放进去即可，或自行改模板里的路径）。两种方式任选：

**方式 1：Let's Encrypt 自动签发（推荐，公共 CA，浏览器全信任）**

```bash
apt install certbot python3-certbot-nginx
# 三个域名一张 SAN 证书（要求 80 端口对外可达）
certbot certonly --nginx \
  -d admin.medflow.kdns.fr -d doctor.medflow.kdns.fr -d patient.medflow.kdns.fr
# 证书自动续期（certbot.timer），到期前 30 天自动签新的
# 生成的证书在 /etc/letsencrypt/live/medflow.kdns.fr/ 下

# 软链到 nginx 模板使用的路径
ln -s /etc/letsencrypt/live/medflow.kdns.fr/fullchain.pem /etc/ssl/medflow/origin.pem
ln -s /etc/letsencrypt/live/medflow.kdns.fr/privkey.pem  /etc/ssl/medflow/origin.key
```

> certbot 自动续期没问题：续签后 nginx 会自动 reload（certbot --nginx 自带 hook）。
> 前提是域名解析不断、80 端口可达。

**方式 2：自有证书（购买的/自签的）**

```bash
mkdir -p /etc/ssl/medflow
# 把证书文件放到服务器上
cp your_cert.pem /etc/ssl/medflow/origin.pem
cp your_key.key  /etc/ssl/medflow/origin.key
chmod 600 /etc/ssl/medflow/origin.key
```

> 自签证书浏览器会报"不安全"，只适合测试；对外正式使用请用方式 1 或购买证书。

**Cloudflare 面板（SSL/TLS 概述）按证书类型选模式：**
- 用 certbot / 购买的公共 CA 证书 → **Full (strict)**（Cloudflare 会校验源站证书有效性，公共 CA 能过）
- 用自签证书 → **Full**（不做校验）
- 若之后关掉小黄云（域名直连服务器）→ 模式无关，不用管

**验证证书装好了：**
```bash
openssl s_client -connect 127.0.0.1:443 -servername admin.medflow.kdns.fr </dev/null 2>/dev/null | grep -E "subject=|issuer="
```

## 五、配置 nginx

```bash
cp deploy/nginx/medflow.conf /etc/nginx/sites-available/medflow.conf
ln -s /etc/nginx/sites-available/medflow.conf /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default   # 删掉默认站点，避免抢 80 端口
nginx -t && systemctl reload nginx
```

## 六、后端服务化（systemd）

```bash
cp deploy/medflow-backend.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now medflow-backend
systemctl status medflow-backend   # 确认 active (running)
journalctl -u medflow-backend -f   # 看日志
```

> 修改 `medflow-backend.service` 里的 `User`、`WorkingDirectory` 以匹配实际部署路径。

## 七、防火墙

```bash
# Cloudflare 只会从它自己的 IP 段访问你的 443/80
ufw allow 22/tcp
ufw allow 443/tcp   # 可选：只放行 Cloudflare IP 段（https://www.cloudflare.com/ips/）
ufw allow 80/tcp
ufw enable
```
8000 端口**不要**对外网开放（nginx 本机反代即可）。

## 八、验证清单

1. `curl -k https://admin.medflow.kdns.fr/api/v1/` → 有 JSON 响应（跳过证书校验只测联通）
2. 浏览器访问三个域名 → 页面正常、无混合内容警告
3. 登录 admin / doctor / patient → 无跨域报错（DevTools Network 里 API 请求是 same-origin `/api/v1/...`）
4. 上传头像 → 访问 `https://admin.medflow.kdns.fr/uploads/...` 能显示
5. 刷新深链接（如 `/admin/doctors`）→ 不 404（history 路由回退生效）
6. `systemctl status medflow-backend` → active；重启服务器后服务自动拉起

## 版本发布（后续）

```bash
pnpm build:admin && pnpm build:doctor && pnpm build:patient
scp -r packages/*/dist root@107.172.243.182:/var/www/medflow/   # 覆盖对应目录
```
后端改动：本地改完 → 推到服务器 → `systemctl restart medflow-backend`。
