# -*- coding: utf-8 -*-
"""修复：员工用例图、单实体ER、整体ER、模块图、流程图"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle, Polygon, FancyBboxPatch, Circle
import matplotlib.lines as mlines
import math, os

plt.rcParams["font.family"] = "Microsoft YaHei"
plt.rcParams["axes.unicode_minus"] = False

OUT = os.path.join(os.path.dirname(__file__), "figs")
EC = "#2f6f3e"; EFILL = "#f2f8ee"; AFILL = "#fdf6e3"; BOXF = "#eef4ea"; FB = "#3a5f7d"


def new_ax(w, h, xlim=100, ylim=100):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    ax.set_xlim(0, xlim); ax.set_ylim(0, ylim); ax.axis("off")
    return fig, ax


def connect(ax, x1, y1, x2, y2, lw=1.0, ls="-"):
    ax.add_line(mlines.Line2D([x1, x2], [y1, y2], color=EC, lw=lw, ls=ls, zorder=1))


def actor(ax, x, y, label, s=1.0):
    r = 2.2 * s
    ax.add_patch(Circle((x, y + 3.2 * s), r, fill=False, lw=1.4, ec=EC, zorder=3))
    ax.add_line(mlines.Line2D([x, x], [y + 1.0 * s, y - 2.6 * s], color=EC, lw=1.4, zorder=3))
    ax.add_line(mlines.Line2D([x - 1.8 * s, x + 1.8 * s], [y - 0.4 * s, y - 0.4 * s], color=EC, lw=1.4, zorder=3))
    ax.add_line(mlines.Line2D([x, x - 1.5 * s], [y - 2.6 * s, y - 5.2 * s], color=EC, lw=1.4, zorder=3))
    ax.add_line(mlines.Line2D([x, x + 1.5 * s], [y - 2.6 * s, y - 5.2 * s], color=EC, lw=1.4, zorder=3))
    ax.text(x, y - 7.6 * s, label, ha="center", va="top", fontsize=11, zorder=3)


def usecase(ax, x, y, w, h, text, fs=10):
    ax.add_patch(Ellipse((x, y), w, h, fill=True, fc=EFILL, ec=EC, lw=1.3, zorder=2))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, zorder=3)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), bbox_inches="tight", facecolor="white")
    plt.close(fig); print("saved", name)


# ============ 图2.3 员工用例图（选择性连线） ============
def fig_staff_usecase():
    fig, ax = new_ax(10.5, 7.8)
    ax.add_patch(Rectangle((20, 5), 70, 88, fill=False, ec="#888", lw=1.3))
    ax.text(55, 95.5, "养殖场员工端", ha="center", fontsize=12.5, weight="bold")
    ucs = [
        (55, 86, "登录系统"),
        (55, 74, "查看工作台 / 今日任务"),
        (38, 62, "提交饲喂记录"),
        (72, 62, "登记配种 / 产犊"),
        (38, 50, "登记防疫 / 诊疗"),
        (72, 50, "查看繁育预警"),
        (38, 38, "进货登记"),
        (72, 38, "申请物资领用"),
        (55, 24, "查看通知 / 站内消息"),
    ]
    for x, y, t in ucs:
        usecase(ax, x, y, 30, 10.5, t, fs=9.5)
    actor(ax, 7, 62, "饲喂员")
    actor(ax, 7, 44, "繁育员")
    actor(ax, 7, 26, "兽医")
    actor(ax, 93, 44, "库管员")
    # 饲喂员
    for x, y in [(55, 86), (55, 74), (38, 62), (38, 38), (55, 24)]:
        connect(ax, 9.5, 58, x - 15, y)
    # 繁育员
    for x, y in [(55, 86), (55, 74), (72, 62), (72, 50), (55, 24)]:
        connect(ax, 9.5, 40, x - 15, y)
    # 兽医
    for x, y in [(55, 86), (55, 74), (38, 50), (72, 38), (55, 24)]:
        connect(ax, 9.5, 22, x - 15, y)
    # 库管员
    for x, y in [(55, 86), (55, 74), (38, 38), (72, 38), (55, 24)]:
        connect(ax, 90.5, 40, x + 15, y)
    save(fig, "fig2_3_usecase_staff.png")


# ============ 单实体 ER（放射状属性） ============
def er_single(name, entity, attrs, w=9.8, h=6.2):
    fig, ax = new_ax(w, h)
    ex, ey = 50, 50
    n = len(attrs)
    ax.add_patch(Rectangle((ex - 17, ey - 6), 34, 12, fill=True, fc=BOXF, ec=EC, lw=1.5, zorder=3))
    ax.text(ex, ey, entity, ha="center", va="center", fontsize=11.5, weight="bold", zorder=4)
    for i, a in enumerate(attrs):
        ang = 2 * math.pi * i / n + math.pi / n
        ax_ = ex + 36 * math.cos(ang) * 1.25
        ay = ey + 24 * math.sin(ang)
        ax.add_patch(Ellipse((ax_, ay), 14.5, 9.5, fill=True, fc=AFILL, ec=EC, lw=1.1, zorder=3))
        ax.text(ax_, ay, a, ha="center", va="center", fontsize=9.2, zorder=4)
        sx = ex + 17 * math.cos(ang) if abs(math.cos(ang)) > 0.35 else ex
        sy = ey + 6 * math.sin(ang) if abs(math.sin(ang)) > 0.35 else ey
        connect(ax, sx, sy, ax_, ay)
    save(fig, name)


# ============ 图3.6 整体 ER（栅格布局） ============
def fig_er_overall():
    fig, ax = new_ax(13.5, 8.2, xlim=138, ylim=100)

    def ent(x, y, text, w=20, h=8):
        ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fill=True, fc=BOXF, ec=EC, lw=1.4, zorder=3))
        ax.text(x, y, text, ha="center", va="center", fontsize=10.5, weight="bold", zorder=4)
        return (x, y, w, h)

    def rel(x, y, text, w=14, h=9):
        ax.add_patch(Polygon([(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)],
                             fill=True, fc=AFILL, ec=EC, lw=1.2, zorder=3))
        ax.text(x, y, text, ha="center", va="center", fontsize=8.8, zorder=4)

    def card(x, y, t):
        ax.text(x, y, t, fontsize=9, zorder=4, weight="bold", color="#555")

    # 第1行 y=88：用户(14) 养殖场(50) 圈舍(88) 防疫/诊疗(124)
    # 第2行 y=52：领用记录(14) 饲喂记录(50) 畜禽档案(88) 饲喂方案(124)
    # 第3行 y=16：物资库存(14) 销售订单(50) 配种记录(88) 产犊记录(124)
    ent(14, 88, "用户"); ent(50, 88, "养殖场"); ent(88, 88, "圈舍"); ent(124, 88, "防疫/诊疗")
    ent(14, 52, "领用记录"); ent(50, 52, "饲喂记录"); ent(88, 52, "畜禽档案"); ent(124, 52, "饲喂方案")
    ent(14, 16, "物资库存"); ent(50, 16, "销售订单"); ent(88, 16, "配种记录"); ent(124, 16, "产犊记录")

    # 1 养殖场1—拥有—n 用户
    connect(ax, 21, 88, 43, 88); rel(32, 88, "拥有"); card(24, 90, "n"); card(40, 90, "1")
    # 2 养殖场1—包含—n 圈舍
    connect(ax, 57, 88, 81, 88); rel(69, 88, "包含"); card(60, 90, "1"); card(78, 90, "n")
    # 3 圈舍1—容纳—n 畜禽档案
    connect(ax, 88, 84, 88, 56); rel(88, 70, "容纳"); card(90, 81, "1"); card(90, 59, "n")
    # 4 畜禽档案1—产生—n 饲喂记录
    connect(ax, 78, 52, 62, 52); rel(70, 52, "产生"); card(75, 54, "1"); card(65, 54, "n")
    # 5 畜禽档案1—配种—n 配种记录
    connect(ax, 88, 48, 88, 20); rel(88, 34, "配种"); card(90, 45, "1"); card(90, 23, "n")
    # 6 配种记录1—分娩—n 产犊记录
    connect(ax, 98, 16, 114, 16); rel(106, 16, "分娩"); card(101, 18, "1"); card(111, 18, "n")
    # 7 饲喂方案1—执行—n 饲喂记录（折线经 y=40）
    ax.add_line(mlines.Line2D([124, 124, 62, 50, 50], [48, 40, 40, 40, 48], color=EC, lw=1.0, zorder=1))
    rel(87, 40, "执行"); card(120, 44, "1"); card(53, 44, "n")
    # 8 防疫/诊疗 n—关联—1 畜禽档案（斜线）
    connect(ax, 117, 83, 95, 56); rel(107, 71, "关联", w=14, h=9)
    card(113, 79, "n"); card(98, 60, "1")
    # 9 养殖场1—持有—n 物资库存（折线经 x=34 通道，避开领用记录）
    ax.add_line(mlines.Line2D([46, 34, 34, 24], [84, 68, 24, 16], color=EC, lw=1.0, zorder=1))
    rel(34, 68, "持有"); card(43, 80, "1"); card(27, 22, "n")
    # 10 物资库存1—生成—n 领用记录
    connect(ax, 14, 20, 14, 48); rel(14, 34, "生成"); card(16, 23, "1"); card(16, 45, "n")
    # 11 销售订单 m—出栏—n 畜禽档案（斜线）
    connect(ax, 56, 20, 82, 48); rel(69, 34, "出栏", w=14, h=9)
    card(58, 24, "m"); card(79, 44, "n")
    save(fig, "fig3_6_er_overall.png")


# ============ 图3.1 模块图（业务模块双列） ============
def fig_modules():
    fig, ax = new_ax(12.5, 7.6, xlim=130, ylim=100)

    def box(x, y, w, h, text, fc=BOXF, fs=10.5, weight="normal", ec=EC, z=2):
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                    boxstyle="round,pad=0.3", fc=fc, ec=ec, lw=1.2, zorder=z))
        ax.text(x, y, text, ha="center", va="center", fontsize=fs, weight=weight, zorder=z + 1)

    box(65, 93, 44, 8, "智能养殖信息管理系统", fc="#dde9d2", fs=13, weight="bold")
    l1 = [(16, "公共模块"), (47, "养殖场主模块"), (81, "养殖业务模块"), (114, "系统管理模块")]
    for x, t in l1:
        box(x, 74, 25, 7, t, fc="#e8f1df", fs=11, weight="bold")
        connect(ax, 65, 89, x, 77.5, lw=1.1)
    cols = {
        16: ["登录注册", "数据大屏", "审核通知中心", "站内消息"],
        47: ["养殖场信息", "员工管理", "岗位薪资配置", "多畜种导航"],
        114: ["用户管理", "角色管理", "菜单管理", "字典管理", "日志管理", "通知公告"],
    }
    for x, items in cols.items():
        n = len(items)
        h = 7.0; gap = (58 - (n * h)) / max(n - 1, 1) if n > 1 else 0
        for i, it in enumerate(items):
            y = 60 - i * (h + gap)
            box(x, y, 22, h, it, fc="white", fs=9.5)
            connect(ax, x, y + h / 2, x, y + h / 2 + gap, lw=1.0)
        connect(ax, x, 70.5, x, 60 + h / 2 + 0.8, lw=1.0)
    # 养殖业务模块：双列 4+4
    bx = 81
    left = ["圈舍管理", "畜禽档案", "饲喂管理", "繁育管理"]
    right = ["防疫诊疗", "物资库存", "销售财务", "数据统计"]
    h = 7.0; gap = 3.2
    for i, it in enumerate(left):
        y = 60 - i * (h + gap)
        box(bx - 12, y, 21, h, it, fc="white", fs=9.5)
        connect(ax, bx - 12, y + h / 2, bx - 12, y + h / 2 + gap, lw=1.0)
    for i, it in enumerate(right):
        y = 60 - i * (h + gap)
        box(bx + 12, y, 21, h, it, fc="white", fs=9.5)
        connect(ax, bx + 12, y + h / 2, bx + 12, y + h / 2 + gap, lw=1.0)
    connect(ax, bx, 70.5, bx, 66, lw=1.0)
    connect(ax, bx - 12, 66, bx + 12, 66, lw=1.0)
    connect(ax, bx - 12, 66, bx - 12, 63.5, lw=1.0)
    connect(ax, bx + 12, 66, bx + 12, 63.5, lw=1.0)
    save(fig, "fig3_1_modules.png")


# ============ 图4.1 审核流程图（修复裁剪） ============
def fig_audit_flow():
    fig, ax = new_ax(8.6, 10.5)

    def box(x, y, w, h, text, fc="#eef4ea"):
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                    boxstyle="round,pad=0.3", fc=fc, ec=EC, lw=1.3))
        ax.text(x, y, text, ha="center", va="center", fontsize=10.5)

    def diamond(x, y, w, h, text):
        ax.add_patch(Polygon([(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)],
                             fill=True, fc="#fdf6e3", ec=EC, lw=1.3))
        ax.text(x, y, text, ha="center", va="center", fontsize=10)

    def arr(x1, y1, x2, y2, label="", loff=(3, 0)):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=EC, lw=1.4))
        if label:
            ax.text((x1 + x2) / 2 + loff[0], (y1 + y2) / 2 + loff[1], label, fontsize=10)

    box(50, 95, 34, 7, "员工提交业务单据")
    arr(50, 91.5, 50, 85.5)
    box(50, 82, 40, 7, "后端校验（防重 / 库存 / 权限）")
    arr(50, 78.5, 50, 72.5)
    box(50, 69, 30, 7, "写入待审核记录")
    arr(50, 65.5, 50, 59.5)
    box(50, 56, 30, 7, "通知场主审核")
    arr(50, 52.5, 50, 46.5)
    diamond(50, 39, 30, 13, "审核是否通过？")
    arr(35, 39, 16, 39); ax.text(24, 41.5, "通过", fontsize=10)
    arr(65, 39, 84, 39); ax.text(73, 41.5, "驳回", fontsize=10)
    box(16, 26, 26, 7, "更新为审核通过")
    arr(16, 39, 16, 29.5)
    box(84, 26, 28, 7, "记录驳回原因")
    arr(84, 39, 84, 29.5)
    arr(16, 22.5, 16, 15)
    arr(84, 22.5, 84, 15)
    box(16, 11.5, 28, 7, "联动库存增减")
    box(84, 11.5, 28, 7, "站内消息通知员工")
    arr(30, 11.5, 70, 11.5)
    box(50, 3.5, 24, 6, "流程结束", fc="#dde9d2")
    arr(50, 8, 50, 6.5)
    save(fig, "fig4_1_audit_flow.png")


fig_staff_usecase()
er_single("fig3_2_er_user.png", "用户 sys_user",
          ["用户ID", "用户名", "密码", "真实姓名", "手机号", "用户类型", "岗位", "所属养殖场"])
er_single("fig3_3_er_animal.png", "畜禽档案",
          ["档案ID", "耳标", "畜种", "品种", "性别", "出生日期", "生长阶段", "状态", "来源"])
er_single("fig3_4_er_feeding.png", "饲喂记录",
          ["记录ID", "饲喂日期", "时段", "圈舍", "计划量", "实际量", "成本", "审核状态"])
er_single("fig3_5_er_mating.png", "配种记录",
          ["记录ID", "母畜耳标", "公畜耳标", "配种日期", "配种方式", "状态", "预产日期", "孕检结果"])
fig_er_overall()
fig_modules()
fig_audit_flow()
print("ALL FIXED")
