<div align="center">
  <img src="icon.ico" width="80" height="80" alt="PowerOSD Logo">
  <h1>⚡ PowerOSD</h1>
  <p>
    <b>基于 HWiNFO64 的超轻量桌面实时功率监控 OSD 小组件</b><br>
    <i>A lightweight, zero-bloat real-time power monitor OSD widget based on HWiNFO64.</i>
  </p>

  <p>
    <a href="#-中文说明">🇨🇳 中文说明</a> •
    <a href="#-english-documentation">🇺🇸 English Documentation</a>
  </p>

  ![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D6?style=flat-square&logo=windows)
  ![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python)
  ![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
  ![Lightweight](https://img.shields.io/badge/RAM-%3C20MB-success?style=flat-square)
</div>

---

## 🇨🇳 中文说明

### 📖 项目简介
**PowerOSD** 是一款基于 **HWiNFO64** 打造的轻量化桌面功率显示 OSD（On-Screen Display）小组件。

相比于传统复杂臃肿的硬件监控软件（如 RTSS + MSI Afterburner 或 AIDA64 传感器面板），**PowerOSD 彻底告别了繁琐的图层与排版配置**。它奉行极简主义，剥离了所有冗余传感器干扰，只为你实时呈现最核心的 **CPU 功率**、**GPU 功率** 与 **机器总功率**。无论是日常办公能效观察、笔记本续航调优，还是高负载烤机测试，都能做到一目了然、随开随关。

### ✨ 核心优势
* 🎯 **纯粹极简，拒绝臃肿**：只显示最基础、最核心的功率信息（CPU / GPU / 整机功耗），无需像传统监控软件那样进行繁琐的界面与字体调试。
* 🔗 **进程联动，随开随关**：启动 `PowerOSD` 时自动在后台静默拉起 HWiNFO64；右键关闭悬浮窗时，自动同步清理后台 HWiNFO64 进程，实现**零后台残留**。
* 🎨 **现代原生视觉**：采用 Catppuccin 暗色系高对比配色，调用 Windows 11 DWM 原生圆角 API 并支持高分屏 DPI 自适应，字体锐利不发虚。
* 🪶 **极致轻量，零性能损耗**：纯 Python 标准库实现，内存级注册表读取（突破 HWiNFO64 免费版 12 小时共享内存限制），CPU 占用低于 `0.05%`。
* ⚙️ **开箱即用，轻松定制**：首次运行自动引导绑定路径并生成 `config.json`，支持随时修改透明度、配色及监控条目。

### 🚀 快速开始

#### 第一步：配置 HWiNFO64（仅首次需要）
1. 打开 **HWiNFO64 传感器状态** 窗口，点击右下角的 **齿轮图标（设置）**。
2. 切换到顶部的 **HWiNFO 小工具 (HWiNFO Gadget)** 选项卡，勾选 **启用报告到小工具 (Enable reporting to Gadget)**。
3. 在列表中分别点击 **`CPU 封装功率`**、**`GT 核心功率`**（或独显 `GPU 功率`）、**`系统总功率`**，并勾选下方的 **在小工具中报告值 (Report value in Gadget)**。
4. 点击右下角 **主要设置 (Main Settings)**，勾选 **启动时最小化主窗口**、**启动时最小化传感器** 与 **仅显示传感器**，点击确定并正常退出一次 HWiNFO64 以保存配置。

#### 第二步：运行 PowerOSD
* **方式 A（免安装可执行版）**：前往 [Releases](../../releases) 页面下载最新版的 `PowerOSD.exe`，双击即可运行。
* **方式 B（Python 源码版）**：确保已安装 Python 3.8+，直接双击运行 `PowerOSD.pyw`。
* *(注：首次运行时若未检测到默认路径下的 HWiNFO64，程序会弹窗引导你选择一次 `HWiNFO64.exe` 的位置，并自动保存在 `config.json` 中。)*

#### 💡 进阶可选：配置全程免 UAC 弹窗（推荐）
为了让普通权限的 `PowerOSD` 在启动和关闭时无需弹出 Windows 管理员确认框（UAC），只需以**管理员身份**打开 PowerShell，运行一次以下命令（将第一行路径修改为你的实际路径）：
```powershell
$hwDir = "C:\Program Files\HWiNFO64"
$act1 = New-ScheduledTaskAction -Execute "$hwDir\HWiNFO64.exe" -WorkingDirectory $hwDir
Register-ScheduledTask -TaskName "StartHWiNFO_Silent" -Action $act1 -RunLevel Highest -Force
$act2 = New-ScheduledTaskAction -Execute "taskkill.exe" -Argument "/IM HWiNFO64.exe"
Register-ScheduledTask -TaskName "StartHWiNFO_Silent_Kill" -Action $act2 -RunLevel Highest -Force
