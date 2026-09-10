#!/bin/bash

set -u

log_file="/app/logs/upload_to_gdrive.log"
mkdir -p "$(dirname "$log_file")"
exec >>"$log_file" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 腳本啟動，參數數量=$#"

if [ "$#" -lt 2 ]; then
    echo "用法: $0 <record_name> <file_path> [save_type]" >&2
    exit 2
fi

record_name="$1"
file_path="$2"
remote_dir="myw:DouyinLiveRecorder"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] record_name=$record_name file_path=$file_path"

if [[ "$file_path" == *"%03d"* && ! -e "${file_path//%03d/*}" ]]; then
    converted_file_path="${file_path%.*}.mp4"
    if compgen -G "${converted_file_path//%03d/*}" >/dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 找不到原始分段檔，改用轉檔後檔案：$converted_file_path"
        file_path="$converted_file_path"
    fi
fi

if ! command -v rclone >/dev/null 2>&1; then
    echo "找不到 rclone，請先安裝並執行 rclone config" >&2
    exit 1
fi
echo "[$(date '+%Y-%m-%d %H:%M:%S')] rclone=$(command -v rclone)"

files=()
if [[ "$file_path" == *"%03d"* ]]; then
    glob_pattern="${file_path//%03d/*}"
    while IFS= read -r matched_file; do
        files+=("$matched_file")
    done < <(compgen -G "$glob_pattern" || true)
else
    files=("$file_path")
fi

if [ "${#files[@]}" -eq 0 ]; then
    echo "找不到要上傳的檔案：$file_path" >&2
    exit 1
fi
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 待上傳檔案數量=${#files[@]}"

for upload_file in "${files[@]}"; do
    if [ ! -s "$upload_file" ]; then
        echo "略過不存在或空白檔案：$upload_file" >&2
        continue
    fi

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 開始上傳：$upload_file"
    rclone copyto "$upload_file" \
        "$remote_dir/$(basename "$upload_file")" \
        --transfers 1 \
        --checkers 4 \
        --multi-thread-streams 4 \
        --drive-chunk-size 64M \
        --retries 3 \
        --low-level-retries 10 \
        --log-file=/app/logs/rclone.log \
        --log-level=INFO

    if [ "$?" -ne 0 ]; then
        echo "上傳失敗：$upload_file" >&2
        exit 1
    fi
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] rclone 上傳成功：$upload_file"

    if rm -f "$upload_file"; then
        echo "已刪除本機檔案：$upload_file"
    else
        echo "Google Drive 上傳成功，但刪除本機檔案失敗：$upload_file" >&2
        exit 1
    fi

done

echo "Google Drive 上傳完成：$remote_dir"
