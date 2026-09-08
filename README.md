# Holly — Blender Rendering

Alchemist 餐厅场景、菜品建模与渲染，以及菜品交互网页预览。此仓库保存脚本、网页源码、验证报告和两张最终预览；完整 Blender、高清 PNG/EXR、纹理和模型导出保存在 GitHub Release。

**[下载全部成果 · v2026.09.08](https://github.com/tangxiya-star/holly-blender-rendering/releases/tag/v2026.09.08)**

仓库为私有；浏览与下载 Release 均需要具有仓库访问权限的 GitHub 账号。

## 最终预览

![Alchemist 餐厅主视角](alchemist/renders/alchemist_hero.png)

<img src="alchemist/food_stress_test/renders/food_final.png" width="400" alt="菜品最终 Cycles 渲染" />

菜品是已完成的建模压力测试；原有评审认为它仍有可见 CG 痕迹，未通过严格照片真实度测试。完整评价见 [critique.md](alchemist/food_stress_test/reports/critique.md)。

## 下载哪一包

压缩包内保留从仓库根目录开始的路径。4 包总计 **573.30 MiB**，包含 **17 个 Blender 场景、41 个渲染文件**、纹理、参考图片及网页模型。`.blend1` 自动备份、依赖目录、构建缓存和本机运行日志不包含在交付包中。

| Release 附件 | 体积 | 内容 |
| --- | ---: | --- |
| [renders.zip](https://github.com/tangxiya-star/holly-blender-rendering/releases/download/v2026.09.08/renders.zip) | 85.31 MiB | 全部餐厅、菜品和原始 dome 渲染，含各轮 PNG 与菜品线性 EXR |
| [restaurant-assets.zip](https://github.com/tangxiya-star/holly-blender-rendering/releases/download/v2026.09.08/restaurant-assets.zip) | 51.22 MiB | 餐厅最终及各里程碑 Blender 场景、原始 dome、纹理和参考图 |
| [food-scenes.zip](https://github.com/tangxiya-star/holly-blender-rendering/releases/download/v2026.09.08/food-scenes.zip) | 276.47 MiB | 菜品 5 轮可编辑 Blender 场景及参考图 |
| [web-assets.zip](https://github.com/tangxiya-star/holly-blender-rendering/releases/download/v2026.09.08/web-assets.zip) | 160.30 MiB | 餐厅与菜品 GLB、对应 web Blender 场景、菜品 split glTF/BIN、餐厅环境 EXR |

另附 `assets-manifest.json`（逐文件大小和 SHA-256、原路径、重复文件映射）与 `SHA256SUMS.txt`（附件校验值）。网页预览的 glTF/BIN 与导出目录内容一致，因此只上传一份，由恢复脚本重建网页使用的副本，减少约 26.76 MiB 重复数据。

## 恢复全部成果

安装 GitHub CLI 和 Python 3，使用有仓库访问权限的账号登录，然后运行：

```sh
gh auth login
gh repo clone tangxiya-star/holly-blender-rendering
cd holly-blender-rendering
python3 tools/restore_assets.py
```

脚本下载固定版本 `v2026.09.08`，验证压缩包和每个文件的 SHA-256，再恢复原目录。已有相同文件会跳过；已有不同内容文件会报错，避免覆盖正在修改的作品。也可以用 `--destination /path/to/empty-folder` 恢复到另一个目录。

只下载渲染，或只恢复网页模型：

```sh
python3 tools/restore_assets.py --archives renders.zip
python3 tools/restore_assets.py --archives web-assets.zip
```

已从 Release 下载附件时，可离线恢复：

```sh
python3 tools/restore_assets.py --from-dir /path/to/downloads
```

手动恢复时，在仓库根目录解压所需 ZIP；要运行菜品网页，再把 `alchemist/food_stress_test/web_exports/food_web.gltf` 与 `food_web_*.bin` 复制到 `alchemist/food_web_preview/public/model/`。自动恢复脚本会完成这一步。

## 打开与运行

- 餐厅最终可编辑场景：`alchemist/alchemist_05_final.blend`。
- 菜品最终可编辑场景：`alchemist/food_stress_test/food_final.blend`。
- 餐厅使用、相机与重建说明：[alchemist/README.md](alchemist/README.md)。
- 菜品各轮渲染与重建说明：[food_stress_test/README.md](alchemist/food_stress_test/README.md)。
- 菜品交互网页说明：[food_web_preview/README.md](alchemist/food_web_preview/README.md)。

网页模型恢复后，使用 Node.js 22.13.0 或更新版本运行：

```sh
cd alchemist/food_web_preview
npm ci
npm run dev
```

网页保留已有 Sites 工程配置。此 Release 归档现有网页源码和模型，不代表重新部署；浏览器材质近似原 Cycles 材质。餐厅 GLB 使用时还需加载 `alchemist/textures/restaurant_environment.exr`。

历史报告和构建快照保留当时的本机路径、结果与来源哈希；它们是原始记录。当前活动脚本的少量绝对工作区路径已改为根据脚本位置定位。此发布未重新渲染场景。

## 后续保存建议

Git 继续保存脚本、说明、报告与少量最终预览；Blender、模型、高清图和视频按里程碑添加新的 Release，保持已发布附件和校验清单不变。GitHub Release 每个附件需小于 2 GiB（[官方文档](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)）。

频繁多人编辑的源场景可考虑 Git LFS；它按完整文件版本累计存储，并计量下载带宽，需考虑配额（[Git LFS 计量说明](https://docs.github.com/en/billing/concepts/product-billing/git-lfs)）。当前这种阶段成果归档适合使用 Release。
