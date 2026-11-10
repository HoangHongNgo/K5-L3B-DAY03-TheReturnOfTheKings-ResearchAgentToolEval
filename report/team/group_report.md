# Báo cáo nhóm — Day 03 Research Agent Tool Eval

> Báo cáo gồm 2 phần có hạn khác nhau:
> - **Phần A (mục 2)** — giới thiệu agent, ngắn gọn 1 trang. **Xong trước Team showdown (16:30)** để team khác hiểu nhanh agent có tool gì, làm được gì. Có thể làm thêm poster `report/team/poster.html` hoặc `poster.svg`.
> - **Phần B (mục 3–7)** — chi tiết và bằng chứng, dựa trên log thật. Hoàn thiện trước deadline nộp bài.
>
> Mỗi bảng phải trỏ được tới file thật: run JSON, transcript, commit. Cách chấm xem [RUBRIC.md](../../RUBRIC.md).

## 1. Thông tin nhóm

- Tên nhóm: TheReturnOfTheKings
- Thành viên và phân công: xem [TEAM.md](../../TEAM.md)
- Provider/model dùng cho v0: OpenRouter / `openai/gpt-4o-mini`.

## 2. Mục tiêu và cách tiếp cận — PHẦN A: Giới thiệu agent

### A1. Agent này làm được gì

Agent hỗ trợ tìm tin web, bài đăng mạng xã hội và bài báo học thuật; đọc URL, tra chính sách nội bộ và định dạng bản tóm tắt. Khi thiếu thông tin, agent cần hỏi lại; việc gửi Telegram chỉ được thực hiện sau khi người dùng duyệt đúng nội dung.

**Cách chạy UI:**

Từ `starter_v0/`: cài `pip install -r requirements.txt`, cấu hình `.env` theo `docs/TOOL-SETUP.md`, rồi chạy `streamlit run app.py`. Dependency Streamlit đã có trong `starter_v0/requirements.txt`. UI ghi log vào `starter_v0/transcripts/` và hiển thị kết quả tool, kể cả lỗi.

**Link dùng thử (deploy):**

URL dùng thử tạm thời: https://era-victory-periodic-broad.trycloudflare.com. Đã kiểm tra `https://era-victory-periodic-broad.trycloudflare.com/_stcore/health` trả `200 ok` ngày 10/11/2026. Đây là Cloudflare Quick Tunnel; link ngừng hoạt động khi UI hoặc tunnel dừng. Lệnh mở tunnel: `cloudflared tunnel --url http://localhost:8501`.

### A2. Tool agent có

> Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại khi thiếu dữ liệu hoặc xin xác nhận | không |
| timeline | lấy bài đăng mới từ một tài khoản | không |
| social_search | tìm bài đăng theo chủ đề | không |
| lookup | tìm kiếm web và tin tức | không |
| fetch | đọc một URL cụ thể | không |
| format | định dạng các mục đã thu thập | không |
| send | gửi nội dung đã được duyệt lên Telegram | không |
| policy | tra chính sách nội bộ | không |
| papers | tìm bài báo học thuật | không |
| paper_text | đọc nội dung bài arXiv | không |

### A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1. Tìm tin web về AI hôm nay.
2. Tóm tắt bài viết này. (Agent cần hỏi URL, sau đó người thử cung cấp URL thật.)
3. Tìm 3 bài đăng mới nhất của tài khoản `sama`.
4. Đăng bản tin này lên Telegram. (Agent cần yêu cầu nội dung và xác nhận trước khi gửi.)

## 3. Giải pháp

> Tóm tắt các thay đổi chính trong `starter_v0/artifacts/system_prompt.md` và `starter_v0/artifacts/tools.yaml`, và tool mới nhóm viết (tên, làm gì, khi nào agent nên gọi).

- `system_prompt.md` (v1–v2): giới hạn phạm vi research, hỏi lại khi thiếu tài khoản/URL, giữ ngữ cảnh khi người dùng sửa yêu cầu và yêu cầu xác nhận trước khi `send`. Prompt quy định hành vi xuyên suốt mọi tool.
- `tools.yaml` (v3): mô tả từng tool theo tình huống dùng/không dùng, chuẩn hóa handle, `query`/`topic`/`timeframe`, `search_type`, và `response_type`. Declaration giúp model chọn đúng tool và điền đúng tham số.

## 4. Kết quả — PHẦN B: Chi tiết và bằng chứng

### B1. Version Evidence

Lấy từ `starter_v0/artifacts/version_log.csv` và `starter_v0/runs/*.json`. Chỉ dùng run có `provider_error_cases == 0` và `measured_cases == total_cases`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline; prompt và tools gốc | Đo trước khi thay đổi | — | 0.65 (13/20) | `starter_v0/runs/v0_B_base_openrouter_20261110T172210098380.json` |
| v1 | `system_prompt.md` | Bỏ chỉ dẫn tự đoán và tự gửi sẽ giảm lỗi routing/boundary | 0.65 (13/20) | 0.90 (18/20) | `starter_v0/runs/v1_B_base_openrouter_20261110T173452631757.json` |
| v2 | `system_prompt.md` | Ghi rõ `response_type` cho `clarify` sẽ sửa lỗi hỏi lại | 0.90 (18/20) | 0.95 (19/20) | `starter_v0/runs/v2_B_base_openrouter_20261110T173620670812.json` |
| v3 | `tools.yaml` | Mô tả rõ cách route, tham số và ranh giới `send` sẽ sửa case còn lại | 0.95 (19/20) | 0.95 (19/20) | `starter_v0/runs/v3_B_base_openrouter_20261110T174041043717.json` |

Mỗi dòng dùng run có `provider_error_cases=0` và `measured_cases=20/20`. V3 sửa được `R12_confirm_before_send`, nhưng `M06_switch_tool` vẫn gọi thêm `social_search` sau khi người dùng chuyển sang chỉ tìm tin web, nên tổng điểm không tăng. Hai bản thử v3 trước đó (`v3_B_base_openrouter_20261110T173832351224.json`, `v3_B_base_openrouter_20261110T173942805034.json`) được giữ làm dấu vết điều chỉnh cùng giả thuyết mô tả tool.

### B2. Failure Analysis

Lấy từ `results[*].result.failures` trong run JSON.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R03_web_news_routing | wrong_tool | `lookup(query="AI news", topic="news", timeframe="day", max_results=5)` | Tool đúng, nhưng `query` cần là `AI`, model thêm "news"; observed mismatch: `wrong_arg_value`. | Làm rõ rằng `query` chỉ chứa chủ đề, còn loại tin đưa vào `topic`. |
| R08_out_of_scope | out_of_scope | `send(text="Nguyên hàm ...")` | Bài toán nguyên hàm ngoài phạm vi vẫn gọi `send`; expected no tool call. | Chặn `send` cho nội dung không phải yêu cầu gửi; trả lời ngoài phạm vi mà không gọi tool. |
| R10_missing_handle | missing_info | `timeline(screenname="sama")` | Tự đoán tài khoản khi người dùng chưa nêu; thiếu `clarify`. | Yêu cầu hỏi lại khi thiếu handle hoặc tên người cụ thể. |
| R11_missing_url | missing_info | `fetch(url="https://example.com/article")` | Tự tạo URL mẫu; thiếu `clarify`. | Yêu cầu hỏi URL thật trước khi gọi `fetch`. |
| R12_confirm_before_send | wrong_boundary | `send(text="Bản tin này")` | Gọi `send` khi chưa có xác nhận; thiếu `clarify`. | Ghi rõ ranh giới xác nhận trước khi gửi. |
| R13_parallel_web_and_tweets | wrong_tool | `lookup(query="AI news", timeframe="day", max_results=5)`; `social_search(query="AI", search_type="Latest", limit=5)` | Cả hai tool đã được gọi, nhưng `lookup` thiếu `topic="news"` và `query` cần là `AI`; observed mismatch: `wrong_arg_value`. | Làm rõ tham số `query`/`topic` của `lookup` khi gọi song song. |
| R14_out_of_scope_coding | out_of_scope | `send(text="Dưới đây là một hàm Python ...")` | Yêu cầu viết code ngoài phạm vi vẫn gọi `send`; expected no tool call. | Giới hạn `send` vào hành động gửi đã được xác nhận. |

Nguồn B2: `starter_v0/runs/v0_B_base_openrouter_20261110T172210098380.json`, `results[*].result`. `failure_type` là nhãn case trong bộ eval; `observed_mismatch` mô tả sai khác thực tế. Vì vậy R03 và R13 có nhãn `wrong_tool` dù tool đã được chọn đúng.

### B3. Team Eval Cases

Liệt kê đúng 10 case trong `starter_v0/data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_similar_posts_by_reference_account | Route tới tool mới; map Andrej Karpathy | `similar_posts(reference_screenname="karpathy")` | `provider_error` — không đo được |
| G02_news_topic_timeframe | Tin xe điện trong tháng này | `lookup(query="xe điện", topic="news", timeframe="month")` | `provider_error` — không đo được |
| G03_posts_about_topic_not_user_timeline | Phân biệt tìm theo chủ đề và timeline | `social_search(query="VinFast")` | `provider_error` — không đo được |
| G04_missing_person_for_timeline | Hỏi lại khi thiếu tài khoản, giữ limit | `clarify(response_type="text")` | `provider_error` — không đo được |
| G05_no_tool_greeting | Lời chào không cần tool | Trả lời không gọi tool | `provider_error` — không đo được |
| G06_multiturn_fill_timeline_account | Bổ sung tài khoản, giữ số lượng qua lượt | `timeline(screenname="satyanadella", limit=4)` | `provider_error` — không đo được |
| G07_multiturn_switch_social_to_web | Đổi social sang web, giữ chủ đề và thời gian | `lookup(query="pin thể rắn", topic="news", timeframe="week")` | `provider_error` — không đo được |
| G08_multiturn_correct_social_search_type | Sửa loại kết quả thành Top qua lượt | `social_search(query="AI agents", search_type="Top")` | `provider_error` — không đo được |
| G09_multiturn_url_after_clarification | Dùng URL đã được bổ sung ở lượt trước | `fetch(url="https://openai.com/index/introducing-gpt-4-1/")` | `provider_error` — không đo được |
| G10_multiturn_confirm_before_telegram_send | Xác nhận trước side effect | `clarify(response_type="yes_no")` | `provider_error` — không đo được |

Run: `starter_v0/runs/v3_B_group_openrouter_20261110T184440643560.json`. Schema hợp lệ và đủ 10 case (5 single turn, 5 multi turn), nhưng OpenRouter trả `APIConnectionError: Connection error` cho cả 10; `provider_error_cases=10`, `measured_cases=0`, `passed_cases=0`. Không diễn giải 0% như điểm chất lượng agent; cần chạy lại khi provider kết nối được để có kết quả đo.
### B4. Live Chat Evidence

Lấy từ `starter_v0/transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Find web news about AI today. | `lookup(query="AI", topic="news", timeframe="day")` | `v3+pcfe354e63035+t3154f5f5b7d9` | Route và args đúng; tool trả `RuntimeError`, không lấy được tin. |
| 2 | Summarize this article for me. | Không có | cùng transcript | Agent hỏi URL bằng text; chưa gọi `clarify` như boundary mong muốn. |
| 3 | https://example.com | `fetch(url="https://example.com")` | cùng transcript | Agent nhận URL và route đúng; tool trả `RuntimeError`, không có nội dung tóm tắt. |
| 4 | Post this digest to Telegram. | Không có | cùng transcript | Agent hỏi nội dung cần gửi, không gọi `send`; chưa gọi `clarify`. |

Nguồn B4: `starter_v0/transcripts/v3_openrouter_20261110T180424128094.transcript.json` (`turns[0..3]`). Đây là 4 lượt từ OpenRouter thật; chưa chứng minh chất lượng tóm tắt do hai tool lấy dữ liệu lỗi. Không có Telegram credentials, nên không có thao tác gửi thật.

### B5a. Required Evidence — Tool mới, unit test, UI

| Item | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Tool mới (`tools/<tên>/`) | `starter_v0/tools/similar_posts/`; registry và declaration | `similar_posts` hỗ trợ reference text và profile từ tài khoản X/Twitter | Xem bảng CP3 chi tiết bên dưới. |
| Unit test tool mới (≥ 3 test/tool) | `starter_v0/tests/test_tools_todo.py`; `pytest -q`: 72 passed, 0 failed, 14 skipped | 5 test của `similar_posts` đều pass | 14 test skipped thuộc challenge của các starter tool, không thuộc tool mới. |
| UI (lệnh chạy + link dùng thử) | `starter_v0/app.py`, `starter_v0/requirements.txt`; link và lệnh ở A1 | UI dùng cùng vòng lặp với `chat.py`, lưu transcript và cho xem tool result; URL công khai trả `200 ok` | Link Quick Tunnel chỉ tồn tại khi UI và tunnel còn chạy; chưa có người ngoài nhóm xác nhận dùng thử câu A3. |

#### CP3 — Tool `similar_posts`

| Item | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Tool mới `similar_posts` | `starter_v0/tools/similar_posts/tool.py`; `starter_v0/tools/similar_posts/TOOL.md`; `starter_v0/tools/__init__.py`; `starter_v0/artifacts/tools.yaml` | Tool tìm và xếp hạng bài đăng X/Twitter tương tự theo một đoạn `reference_text` hoặc hồ sơ nội dung từ các bài gần đây của `reference_screenname`. Điểm xếp hạng kết hợp term coverage (45%), Jaccard overlap (35%) và phrase overlap (20%). Chế độ theo tài khoản dùng một request lấy timeline và một request tìm kiếm. | Tool kiểm tra input; giới hạn `limit` và `timeline_limit` trong khoảng 1–20; loại bài trùng, bài của chính tài khoản tham chiếu và kết quả có điểm dưới 0.15. Khi thiếu key hoặc API lỗi, tool trả error dictionary thay vì làm agent crash. |
| Unit test tool mới — 5 test | `starter_v0/tests/test_tools_todo.py`; kết quả toàn suite: `72 passed, 0 failed, 14 skipped` | Năm test kiểm tra: xếp hạng và query gửi tới API; loại kết quả dưới ngưỡng; tạo profile tài khoản bằng đúng hai request; từ chối reference rỗng mà không gọi mạng; và trả error dictionary khi thiếu `RAPIDAPI_KEY`. Toàn bộ 60 contract test pass. | HTTP được mock bằng `FakeResponse`, nên unit test không dùng API credit hoặc mạng thật. Test kiểm tra cả request gửi đi và dữ liệu trả về. |
| Live smoke test | Chạy trực tiếp `TOOL_FUNCTIONS["similar_posts"]` với `reference_screenname="sama"`, `timeline_limit=5`, `limit=2` | Tool lấy 5 bài gần đây, tạo profile, thực hiện tìm kiếm và trả 2 bài từ tài khoản khác kèm `similarity_score`; luồng hoàn thành không có API error. | Một live test dùng đúng 2 RapidAPI request. Query profile loại các từ chung như `rt`, `today`, `things`, `we` để giảm nhiễu và tiết kiệm quota free tier. |

Nhóm viết **5 unit test** cho `similar_posts`, vượt yêu cầu tối thiểu 3 test/tool. Một lỗi mà unit test bắt được nhưng routing eval không phát hiện là trường hợp model truyền `reference_text` rỗng: model vẫn có thể chọn đúng tên tool nên routing eval xem là đúng, nhưng implementation lỗi có thể gửi một API request vô nghĩa. Test `test_similar_posts_rejects_empty_reference_without_network` xác nhận tool trả `ValueError` dưới dạng error dictionary và không tạo HTTP request nào.

### B5. Bonus Evidence

Chỉ điền nếu nhóm làm bonus (ghi riêng, tối đa 10 điểm). Tool có sẵn (`send`, `policy`, `papers`, `paper_text`) không tự được bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Small Local Model | xem B7 |  |  |
| Hơn 3 tool mới (≥ 4) |  |  |  |
| `send` gửi thật lên Telegram sau xác nhận | transcript |  |  |
| Test challenge (0 skipped / regression test) | `pytest` output |  |  |

Test challenge: số bug tìm được trong tool có sẵn (nếu có), cách sửa, và test regression tương ứng.

### B7. Small Local Model Challenge (bonus)

Chỉ điền nếu nhóm làm bonus này.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  |  |
| v3-<model> | (ollama) | v3 |  |  |  |  |  |
| v3-<model> | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?

## 5. Khó khăn và cách xử lý

> Khó khăn chính và cách nhóm xử lý. Nếu gặp lỗi kỹ thuật (provider lỗi, hết quota API, tool không chạy), mô tả lỗi và dẫn bằng chứng: run JSON, log, ảnh chụp.

- Lần chạy v0 đầu tiên bị OpenRouter trả `403 Key limit exceeded` cho cả 20 case (`starter_v0/runs/v0_B_base_openrouter_20261110T171528337107.json`), nên không dùng làm baseline. Sau khi cập nhật key, run v0 ở B1 có `provider_error_cases=0`, `measured_cases=20/20`; preflight OpenRouter pass.
- Trong live chat v3, `lookup` thiếu `TAVILY_API_KEY` và `fetch` thiếu `FIRECRAWL_API_KEY`; transcript B4 lưu nguyên lỗi. Agent hỏi URL và nội dung Telegram bằng text thay vì `clarify`, cho thấy phản hồi nghe hợp lý vẫn có thể sai về tool boundary.

## 6. Tổng hợp đóng góp

Danh sách ba thành viên có trong [TEAM.md](../../TEAM.md). Các báo cáo cá nhân đã được tạo theo MSSV; mỗi thành viên cần xác nhận phân công, đóng góp và commit của mình trước khi nộp.

## 7. Hạn chế và hướng cải thiện — B6. Reflection

- `system_prompt.md` chứa quy tắc hành vi chung: không tự đoán thông tin, không dùng `send` để trả lời chat, xác nhận nội dung trước khi gửi, và tôn trọng sửa đổi ở lượt sau.
- `tools.yaml` chứa điều kiện gọi từng tool và quy ước tham số: handle không có `@`, `topic=news` và `timeframe=day` cho tin hôm nay, `search_type=Top` cho tweet phổ biến, `response_type=yes_no` khi xin xác nhận gửi.
- `R12_confirm_before_send` cần review thủ công vì chấm tự động chỉ kiểm tra `clarify(response_type=yes_no)`, chưa biết câu hỏi đã nêu đúng nội dung cần gửi hay chưa. Tương tự, chấm tự động không xác nhận chất lượng dữ liệu tool trả về.
- Vòng sau sẽ thử quy tắc bỏ nguồn đã bị người dùng hủy ở đa lượt, rồi đo riêng `M06_switch_tool` và toàn bộ base để tránh lỗi hồi quy. V3 vẫn đạt 19/20 vì case này gọi thừa `social_search`.

## 8. Tài liệu tham khảo

-


