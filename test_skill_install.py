#!/usr/bin/env python3
"""
快速测试 Skill 安装功能

测试内容:
1. 测试 ui-ux-pro-max 安装 (使用 .opencode/skills/ui-ux-pro-max 路径)
2. 测试 SKILL.txt 文件支持
3. 验证安装后能否被 SkillDiscovery.discover_all() 发现
"""

import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
import tempfile
import shutil

# 导入必要的类
from opencode_config_manager_fluent import SkillInstaller, SkillDiscovery


def test_ui_ux_pro_max_install():
    """测试 ui-ux-pro-max skill 安装"""
    print("\n" + "=" * 80)
    print("测试 1: ui-ux-pro-max skill 安装")
    print("=" * 80)

    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        target_dir = Path(temp_dir) / "skills"
        target_dir.mkdir(parents=True, exist_ok=True)

        print(f"目标目录: {target_dir}")

        # 安装 skill
        print("\n开始安装...")
        success, message = SkillInstaller.install_from_github(
            owner="nextlevelbuilder",
            repo="ui-ux-pro-max-skill",
            branch="main",
            target_dir=target_dir,
            subdir=".opencode/skills/ui-ux-pro-max",
            progress_callback=lambda msg: print(f"  进度: {msg}"),
        )

        print(f"\n结果: {'✓ 成功' if success else '✗ 失败'}")
        print(f"消息: {message}")

        if success:
            # 检查安装的文件
            installed_skills = list(target_dir.iterdir())
            print(f"\n已安装的 skills: {[s.name for s in installed_skills]}")

            # 检查 SKILL 文件
            for skill_dir in installed_skills:
                if skill_dir.is_dir():
                    skill_md = skill_dir / "SKILL.md"
                    skill_txt = skill_dir / "SKILL.txt"
                    meta_file = skill_dir / ".skill-meta.json"

                    print(f"\n{skill_dir.name}:")
                    print(f"  SKILL.md: {'✓' if skill_md.exists() else '✗'}")
                    print(f"  SKILL.txt: {'✓' if skill_txt.exists() else '✗'}")
                    print(f"  .skill-meta.json: {'✓' if meta_file.exists() else '✗'}")

        return success


def test_skill_discovery():
    """测试 SkillDiscovery.discover_all() 是否支持 SKILL.txt"""
    print("\n" + "=" * 80)
    print("测试 2: SkillDiscovery 支持 SKILL.txt")
    print("=" * 80)

    # 创建临时目录结构
    with tempfile.TemporaryDirectory() as temp_dir:
        skills_dir = Path(temp_dir) / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        # 创建测试 skill (使用 SKILL.txt)
        test_skill_dir = skills_dir / "test-skill"
        test_skill_dir.mkdir()

        skill_txt = test_skill_dir / "SKILL.txt"
        skill_txt.write_text(
            """# Test Skill

A test skill for validation.

## Description
This is a test skill.
""",
            encoding="utf-8",
        )

        print(f"创建测试 skill: {test_skill_dir}")
        print(f"  SKILL.txt: ✓")

        # 临时修改 SKILL_PATHS 来测试
        original_paths = SkillDiscovery.SKILL_PATHS.copy()
        SkillDiscovery.SKILL_PATHS = {"test": skills_dir}

        try:
            # 发现 skills
            discovered = SkillDiscovery.discover_all()
            print(f"\n发现的 skills: {len(discovered)}")

            for skill in discovered:
                print(f"  - {skill.name} (来源: {skill.source})")
                print(f"    路径: {skill.path}")
                print(f"    描述: {skill.description[:50]}...")

            success = len(discovered) > 0
            print(f"\n结果: {'✓ 成功' if success else '✗ 失败'}")

            return success
        finally:
            # 恢复原始路径
            SkillDiscovery.SKILL_PATHS = original_paths


def main():
    """主函数"""
    print("Skill 安装功能测试")
    print("=" * 80)

    results = []

    # 测试 1: ui-ux-pro-max 安装
    try:
        result1 = test_ui_ux_pro_max_install()
        results.append(("ui-ux-pro-max 安装", result1))
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback

        traceback.print_exc()
        results.append(("ui-ux-pro-max 安装", False))

    # 测试 2: SKILL.txt 支持
    try:
        result2 = test_skill_discovery()
        results.append(("SKILL.txt 支持", result2))
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback

        traceback.print_exc()
        results.append(("SKILL.txt 支持", False))

    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)

    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{name}: {status}")

    all_passed = all(r[1] for r in results)
    print(f"\n总体结果: {'✓ 所有测试通过' if all_passed else '✗ 部分测试失败'}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
