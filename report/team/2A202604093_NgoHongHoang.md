# Báo cáo cá nhân — Ngô Hồng Hoàng (2A202604093)

## 1. Thông tin thành viên

- Họ tên: Ngô Hồng Hoàng
- MSSV: 2A202604093
- Vai trò: Trưởng nhóm TheReturnOfTheKings; phụ trách CP1, CP2 và CP5.
- GitHub: [HoangHongNgo](https://github.com/HoangHongNgo)
- Email: chưa cung cấp trong thông tin nhóm.

## 2. Phần việc phụ trách

- **CP1:** Thiết lập thông tin repo nhóm, chạy baseline v0, phân tích lỗi và ghi kết quả vào `version_log.csv` và báo cáo nhóm.
- **CP2:** Tối ưu `system_prompt.md` và `tools.yaml` qua bốn phiên bản v1–v4; chạy base eval, ghi giả thuyết, hash, metric trước/sau và phân tích lỗi còn lại.
- **CP5:** Làm UI Streamlit, chạy live chat, lưu transcript; viết phần giới thiệu agent, hướng dẫn dùng thử và các phần bằng chứng CP1, CP2, CP5 trong báo cáo nhóm; tạo khung báo cáo cá nhân cho các thành viên.
- Với vai trò trưởng nhóm, tổng hợp tiến độ và bằng chứng các checkpoint mình phụ trách trong `TEAM.md` và `report/team/group_report.md`.

## 3. Đóng góp cụ thể

### CP1 — Baseline v0 và phân tích lỗi

Tôi cập nhật thông tin nhóm trong `TEAM.md` và chạy bộ base eval v0 bằng OpenRouter với prompt/tool declaration gốc. Run đầu bị lỗi giới hạn key OpenRouter nên không dùng làm baseline. Run hợp lệ đo đủ 20/20 case, không có lỗi provider và đạt 13/20 (65%). Tôi ghi kết quả vào `version_log.csv` và lập bảng B2 trong báo cáo nhóm cho bảy case FAIL. Các lỗi gồm tự đoán tài khoản/URL, sai tham số `lookup`, dùng `send` sai ngữ cảnh và gửi khi chưa được xác nhận.

### CP2 — Tối ưu bốn phiên bản v1–v4

| Phiên bản | Thay đổi chính | Kết quả base eval |
|---|---|---:|
| v1 | Sửa `system_prompt.md`: bỏ chỉ dẫn tự đoán thông tin và tự gửi; giới hạn phạm vi research, hỏi lại khi thiếu dữ liệu, xin xác nhận trước `send`. | 18/20 (90%) |
| v2 | Quy định `response_type` của `clarify`: `text` cho thông tin thiếu, `yes_no` cho xác nhận gửi. | 19/20 (95%) |
| v3 | Viết lại mô tả trong `tools.yaml`: điều kiện dùng từng tool, quy ước handle và tham số tìm kiếm, ranh giới xác nhận của `send`. | 19/20 (95%) |
| v4 | Bổ sung quy tắc trong `system_prompt.md` để nguồn đã bị hủy ở lượt trước không được kích hoạt lại khi lượt sau chỉ giữ chủ đề. | 20/20 (100%) |

Các run nêu trên đều đo đủ 20 case và có `provider_error_cases=0`. V3 sửa được `R12_confirm_before_send`, nhưng `M06_switch_tool` vẫn gọi thừa `social_search` sau khi người dùng chuyển sang chỉ tìm tin web, nên tổng điểm không tăng. Tôi bổ sung prompt v4 để xác định lại các nguồn còn hiệu lực qua nhiều lượt; run v4 đạt 20/20, gồm cả `M06_switch_tool`. Run kiểm chứng v4 với schema tool v3 cũng đạt 20/20, giúp đối chiếu tác động của thay đổi prompt; một lần chạy chưa chứng minh độ ổn định với mọi cách diễn đạt.

### CP5 — UI, live chat và báo cáo

Tôi tạo `starter_v0/app.py` bằng Streamlit, dùng chung `run_model_tool_loop` với `chat.py`. UI cho phép mở cuộc trò chuyện mới, hiển thị lỗi provider, tool calls và kết quả tool, đồng thời lưu transcript JSON sau mỗi lượt. Tôi thêm Streamlit vào `requirements.txt` và điều chỉnh `chat.py` cho phần dùng chung. Trong báo cáo nhóm, tôi điền phần A (khả năng agent, tool, câu hỏi mẫu, cách chạy UI và link dùng thử tạm thời) cùng phần B về kết quả CP1–CP2, live chat, khó khăn và giới hạn. Tôi tạo các file báo cáo theo MSSV để từng thành viên xác nhận và bổ sung phần việc của mình.

Transcript CP5 có bốn lượt: tìm tin AI trên web; hỏi lại URL khi yêu cầu tóm tắt thiếu địa chỉ; nhận URL và gọi `fetch`; hỏi nội dung trước yêu cầu đăng Telegram. Live chat cho thấy route `lookup`/`fetch` phù hợp, nhưng hai tool trả `RuntimeError`; agent hỏi lại bằng văn bản thay vì gọi `clarify`, và không có lần gửi Telegram thật. Transcript chứng minh luồng tương tác và việc lưu lỗi, chưa chứng minh chất lượng tóm tắt hay gửi thành công.

## 4. Bằng chứng và cách tự kiểm tra

- **CP1–CP2:** Commit [`85252b4bccfb989c67aedd1a8fa1765f6473b935`](https://github.com/HoangHongNgo/K5-L3B-DAY03-TheReturnOfTheKings-ResearchAgentToolEval/commit/85252b4bccfb989c67aedd1a8fa1765f6473b935). PR #1 được merge bằng [`bb01fcd47b6ca878887b5ec65054fca2929a393b`](https://github.com/HoangHongNgo/K5-L3B-DAY03-TheReturnOfTheKings-ResearchAgentToolEval/commit/bb01fcd47b6ca878887b5ec65054fca2929a393b); đây là commit merge của cùng phần việc, không tính thành một lần thực hiện riêng.
- **Bổ sung v4:** Commit [`226a0216f600302dd4923924a17f467da6f2e1b2`](https://github.com/HoangHongNgo/K5-L3B-DAY03-TheReturnOfTheKings-ResearchAgentToolEval/commit/226a0216f600302dd4923924a17f467da6f2e1b2) chứa thay đổi prompt v4, snapshot replay và dữ liệu so sánh phiên bản cho UI.
- **CP5 và báo cáo:** Commit [`c6427498fc4f2824f21f46e74820bf6b182643bd`](https://github.com/HoangHongNgo/K5-L3B-DAY03-TheReturnOfTheKings-ResearchAgentToolEval/commit/c6427498fc4f2824f21f46e74820bf6b182643bd) chứa UI, transcript, cập nhật báo cáo nhóm và các file báo cáo cá nhân.
- **Prompt, declaration và log:** [`system_prompt.md`](../../starter_v0/artifacts/system_prompt.md), [`tools.yaml`](../../starter_v0/artifacts/tools.yaml), [`version_log.csv`](../../starter_v0/artifacts/version_log.csv). Đối chiếu giả thuyết, hash và đường dẫn run với bảng B1 trong [`group_report.md`](group_report.md).
- **Run v0–v3 gốc:** [`v0`](../../starter_v0/runs/v0_B_base_openrouter_20261110T172210098380.json), [`v1`](../../starter_v0/runs/v1_B_base_openrouter_20261110T173452631757.json), [`v2`](../../starter_v0/runs/v2_B_base_openrouter_20261110T173620670812.json), [`v3`](../../starter_v0/runs/v3_B_base_openrouter_20261110T174041043717.json). Kiểm tra `summary.total_cases=20`, `measured_cases=20`, `provider_error_cases=0`; `passed_cases` lần lượt là 13, 18, 19, 19. Các run được cập nhật sau này trong báo cáo nhóm dùng để so sánh bổ sung, không thay thế bằng chứng của commit CP1–CP2.
- **Run v4:** [`run tích hợp`](../../starter_v0/runs/v4_B_base_openrouter_20261110T191602683398.json) và [`run kiểm chứng riêng`](../../starter_v0/runs/v4-isolated_B_base_openrouter_20261110T191807120240.json); cả hai có `summary.total_cases=20`, `measured_cases=20`, `provider_error_cases=0`, `passed_cases=20`. Bảng so sánh được lưu trong [`demo_metrics.json`](../../starter_v0/data/demo_metrics.json).
- **UI và live chat:** [`app.py`](../../starter_v0/app.py), [`requirements.txt`](../../starter_v0/requirements.txt), [`transcript 4 lượt`](../../starter_v0/transcripts/v3_openrouter_20261110T180424128094.transcript.json). Từ `starter_v0/`, cài `pip install -r requirements.txt`, cấu hình `.env` theo `docs/TOOL-SETUP.md`, rồi chạy `streamlit run app.py`. Đối chiếu `turns[*].tool_events` và `turns[*].status` với bảng B4 của báo cáo nhóm.
- **AI và công cụ:** OpenRouter với model `openai/gpt-4o-mini` để chạy agent/eval, Python/Streamlit cho UI và Git để đối chiếu commit. Tôi tự kiểm tra bằng run JSON, transcript và diff commit thay vì chỉ dựa vào câu trả lời của model. Repo chưa có bằng chứng để khẳng định một công cụ AI hỗ trợ viết báo cáo riêng.

## 5. Tự đánh giá

Tôi hoàn thành phần được giao ở CP1, CP2 với bốn phiên bản v1–v4, và phần code UI, live chat, báo cáo thuộc CP5. V4 đạt 20/20 trong run base và run kiểm chứng riêng, khắc phục lỗi `M06_switch_tool` quan sát ở v3. Transcript CP5 vẫn có lỗi tool lấy dữ liệu và lượt hỏi lại chưa dùng `clarify`; cần kiểm tra live chat sau khi cấu hình đủ API và thử thêm nhiều cách diễn đạt trước khi kết luận agent ổn định.

