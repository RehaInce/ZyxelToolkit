
import subprocess
import os
import sys
import json
from typing import List, Optional, Tuple

STATE_FILENAME = ".cli_state.json"


def clear_screen() -> None:
    cmd = "cls" if os.name == "nt" else "clear"
    try:
        os.system(cmd)
    except Exception:
        pass


def read_head(path: str, max_lines: int = 80) -> List[str]:
    # kept for potential future use; no longer used for menu descriptions
    try:
        lines: List[str] = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for _ in range(max_lines):
                line = f.readline()
                if not line:
                    break
                lines.append(line.rstrip("\n"))
        return lines
    except OSError:
        return []


def load_state(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(path: str, state: dict) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        pass


def gather_scripts(script_dir: str) -> List[Tuple[str, str, Optional[str]]]:
    items: List[Tuple[str, str, Optional[str]]] = []
    try:
        for f in os.listdir(script_dir):
            if not f.endswith(".py"):
                continue
            if f == os.path.basename(__file__):
                continue
            if f.startswith("_"):
                continue
            full = os.path.join(script_dir, f)
            # do not extract descriptions anymore; store None
            items.append((f, full, None))
    except FileNotFoundError:
        pass
    items.sort(key=lambda t: t[0].lower())
    return items


def print_menu(items: List[Tuple[str, str, Optional[str]]], last_used: Optional[str], keyword: Optional[str]) -> None:
    clear_screen()
    title = "Script Yöneticisi"
    print(title)
    print("=" * len(title))
    if keyword:
        print(f"Filtre: '{keyword}'")
    print("Komutlar: [s]eç (numara), [f]iltre, [a]rgüman, [h]elp, [r]efresh, [Enter]=son, [q]uit")
    print()
    if not items:
        print("Bu klasörde çalıştırılabilir script bulunamadı.")
        return
    for idx, (name, _path, _desc) in enumerate(items, start=1):
        suffix = ""
        if last_used and os.path.basename(last_used) == name:
            suffix = " [son kullanılan]"
        line = f"{idx:>2}. {name}{suffix}"
        print(line)


def run_script(python_exe: str, src_path: str, script_path: str, args: Optional[str] = None) -> int:
    env = os.environ.copy()
    env['PYTHONPATH'] = src_path + os.pathsep + env.get('PYTHONPATH', '')
    cmd = [python_exe, script_path]
    if args:
        # naive split on spaces; advanced parsing not needed for basic UX
        cmd.extend(args.split())
    try:
        completed = subprocess.run(cmd, env=env)
        return completed.returncode
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        print(f"Çalıştırma hatası: {e}")
        return 1


def main():
    # Root and PYTHONPATH
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    src_path = os.path.join(project_root, 'src')
    sys.path.insert(0, src_path)

    script_dir = os.path.dirname(__file__)
    state_path = os.path.join(script_dir, STATE_FILENAME)
    state = load_state(state_path)
    last_used: Optional[str] = state.get("last_script")

    keyword: Optional[str] = None

    while True:
        all_items = gather_scripts(script_dir)
        visible = all_items
        if keyword:
            kw = keyword.lower()
            visible = [t for t in all_items if kw in t[0].lower() or (t[2] and kw in t[2].lower())]

        print_menu(visible, last_used, keyword)

        if not visible:
            choice = input("Komut (h yardımı için): ").strip()
        else:
            choice = input("Numara/Komut: ").strip()

        if choice.lower() in ("q", "quit", "exit"):
            break

        if choice == "":
            # Enter: run last used if exists
            if last_used and os.path.isfile(last_used):
                rc = run_script(sys.executable, src_path, last_used)
                print(f"\nÇıkış kodu: {rc}")
                input("Devam etmek için Enter...")
                continue
            else:
                print("Son kullanılan script yok.")
                input("Devam etmek için Enter...")
                continue

        if choice.lower() in ("h", "help", "?"):
            print("\nYardım:")
            print("  - Numara: Listeden script çalıştırır.")
            print("  - Enter: Son kullanılan scripti tekrar çalıştırır.")
            print("  - f: Filtre uygular/temizler.")
            print("  - a: Scripti ek argümanlarla çalıştırır.")
            print("  - r: Listeyi yeniler ve filtreyi temizler.")
            print("  - q: Çıkış.")
            input("\nDevam etmek için Enter...")
            continue

        if choice.lower() in ("r", "refresh"):
            keyword = None
            continue

        if choice.lower() in ("f", "filter"):
            new_kw = input("Anahtar kelime (boş = temizle): ").strip()
            keyword = new_kw or None
            continue

        if choice.lower() in ("a", "args"):
            if not visible:
                input("Hiç script yok. Devam için Enter...")
                continue
            num = input("Script numarası: ").strip()
            try:
                idx = int(num)
            except ValueError:
                input("Geçersiz numara. Devam için Enter...")
                continue
            if not (1 <= idx <= len(visible)):
                input("Aralık dışında. Devam için Enter...")
                continue
            args = input("Argümanlar (örn: --foo bar): ").strip()
            name, path, _ = visible[idx - 1]
            rc = run_script(sys.executable, src_path, path, args=args)
            if rc == 0:
                last_used = path
                save_state(state_path, {"last_script": last_used})
            print(f"\n'{name}' çıkış kodu: {rc}")
            input("Devam etmek için Enter...")
            continue

        # Otherwise try numeric selection
        try:
            idx = int(choice)
        except ValueError:
            print("Geçersiz seçim.")
            input("Devam etmek için Enter...")
            continue

        if not (1 <= idx <= len(visible)):
            print("Geçersiz seçim.")
            input("Devam etmek için Enter...")
            continue

        name, path, _ = visible[idx - 1]
        rc = run_script(sys.executable, src_path, path)
        if rc == 0:
            last_used = path
            save_state(state_path, {"last_script": last_used})
        print(f"\n'{name}' çıkış kodu: {rc}")
        input("Devam etmek için Enter...")


if __name__ == '__main__':
    main()
