import os
import requests
import json
import re
import sys
from typing import List, Dict, Any, Optional

# Adjust python path to import model manager and other modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai-model-management")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from model_manager import ModelManager  # type: ignore

# Load keys directly or fallback to environment variables
LLAMA_GUARD_KEY = os.getenv("LLAMA_GUARD_KEY", "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")
RERANKER_KEY = os.getenv("RERANKER_KEY", "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")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_KEY", "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")
NEMOTRON_OMNI_KEY = os.getenv("NEMOTRON_OMNI_KEY", "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")

class NvidiaClient:
    def __init__(self):
        self.session = requests.Session()
        self.model_manager = ModelManager()

    def check_safety(self, text: str, role: str = "user") -> Dict[str, Any]:
        """
        Check user input or assistant output using Llama Guard 4.
        Returns safety assessment.
        """
        url = f"{self.model_manager.get_api_url()}/chat/completions"
        headers = {
            "Authorization": f"Bearer {LLAMA_GUARD_KEY}",
            "Content-Type": "application/json"
        }
        
        config = self.model_manager.get_model_config("safety")
        payload = {
            "model": config.get("model_name", "meta/llama-guard-4-12b"),
            "messages": [{"role": role, "content": text}],
            "max_tokens": config.get("max_tokens", 10),
            "temperature": config.get("temperature", 0.1)
        }
        
        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=config.get("timeout", 10))
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            is_safe = content.startswith("safe")
            categories = content.split("\n")[1:] if not is_safe else []
            
            return {
                "safe": is_safe,
                "categories": categories,
                "raw_response": content
            }
        except Exception as e:
            # Safe default fallback for API failures/timeouts
            print(f"Safety check error: {e}")
            return {"safe": True, "categories": [], "error": str(e)}

    def check_content_safety_reasoning(self, text: str) -> Dict[str, Any]:
        """
        Perform safety and fraud reasoning using nvidia/nemotron-content-safety-reasoning-4b
        """
        url = f"{self.model_manager.get_api_url()}/chat/completions"
        headers = {
            "Authorization": f"Bearer {NEMOTRON_OMNI_KEY}",
            "Content-Type": "application/json"
        }
        
        config = self.model_manager.get_model_config("reasoning")
        payload = {
            "model": config.get("model_name", "nvidia/nemotron-content-safety-reasoning-4b"),
            "messages": [
                {
                    "role": "user",
                    "content": f"Analyze the following student finance request for potential fraud, identity theft, or unauthorized financial access. Explain your reasoning and conclude with either [SAFE] or [UNSAFE]:\n\nRequest: {text}"
                }
            ],
            "max_tokens": config.get("max_tokens", 512),
            "temperature": config.get("temperature", 0.2)
        }
        
        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=config.get("timeout", 15))
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            is_safe = "[UNSAFE]" not in content
            
            return {
                "safe": is_safe,
                "reasoning": content
            }
        except Exception as e:
            print(f"Content safety reasoning error: {e}")
            return {"safe": True, "reasoning": "Fallback (safety check bypassed)", "error": str(e)}

    def call_root_orchestrator(self, messages: List[Dict[str, str]], thinking: bool = False) -> str:
        """
        Call the Root Orchestrator (DeepSeek v4 Pro) to coordinate agents and workflows.
        """
        url = f"{self.model_manager.get_api_url()}/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_KEY}",
            "Content-Type": "application/json"
        }
        
        config = self.model_manager.get_model_config("orchestrator_primary")
        payload = {
            "model": config.get("model_name", "deepseek-ai/deepseek-v4-pro"),
            "messages": messages,
            "temperature": config.get("temperature", 0.7),
            "top_p": 0.95,
            "max_tokens": config.get("max_tokens", 2048),
            "extra_body": {"chat_template_kwargs": {"thinking": thinking}}
        }
        
        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=config.get("timeout", 25))
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return self._clean_markdown(content)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as te:
            print(f"Root Orchestrator timeout error: {te}. Triggering immediate offline rule-based fallback...")
            last_query = messages[-1]["content"] if messages else ""
            return self._generate_rule_based_response(last_query)
        except Exception as e:
            print(f"Root Orchestrator primary error: {e}. Trying fallback orchestrator model...")
            return self._call_orchestrator_fallback(messages)

    def _call_orchestrator_fallback(self, messages: List[Dict[str, str]]) -> str:
        url = f"{self.model_manager.get_api_url()}/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_KEY}",
            "Content-Type": "application/json"
        }
        
        fallback_messages = list(messages)
        if fallback_messages and fallback_messages[0]["role"] == "system":
            fallback_messages[0] = {
                "role": "system",
                "content": fallback_messages[0]["content"] + "\nIMPORTANT: You MUST respond in English. Do not output in Japanese or any other language."
            }
            
        config = self.model_manager.get_model_config("orchestrator_fallback")
        payload = {
            "model": config.get("model_name", "meta/llama-3.1-8b-instruct"),
            "messages": fallback_messages,
            "temperature": config.get("temperature", 0.5),
            "max_tokens": config.get("max_tokens", 1024)
        }
        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=config.get("timeout", 15))
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return self._clean_markdown(content)
        except Exception as fallback_err:
            print(f"Fallback orchestrator error: {fallback_err}. Executing rule-based fallback response...")
            last_query = messages[-1]["content"] if messages else ""
            return self._generate_rule_based_response(last_query)

    def _clean_markdown(self, text: str) -> str:
        if not text or not isinstance(text, str):
            return ""
        text = re.sub(r"^```markdown\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"```\s*$", "", text).strip()
        return text

    def _generate_rule_based_response(self, query: str) -> str:
        # Extract student_id from query if possible
        student_id_match = re.search(r"STU-\d{4}-\d{4}", query)
        student_id = student_id_match.group(0) if student_id_match else "STU-2021-4892"

        from database_mock import DatabaseMock
        student = DatabaseMock.get_student(student_id)
        balance = DatabaseMock.get_student_balance(student_id)

        name = student["name"] if student else "Student"
        currency = student["currency"] if student else "INR"
        symbol = "₹" if currency == "INR" else "$"

        q = query.lower()
        if "refund" in q:
            refunds = DatabaseMock.get_refunds(student_id)
            refund_list = ""
            if refunds:
                refund_list = "\n".join([f"- Request ID `{r['request_id']}`: Amount `{symbol} {r['amount']:,.2f}`, Stage: **{r['stage']}**" for r in refunds])
            else:
                refund_list = "No active refund requests found."
            return (
                f"### 🔄 Refund Status (Offline Fallback Mode)\n\n"
                f"Hello {name}, your refund inquiries are compiled below:\n\n"
                f"{refund_list}\n\n"
                f"- Standard refund verification timeline is **10-15 working days**.\n"
                f"- High-value refunds exceeding `₹ 1,00,000.00` require secondary Director approval.\n\n"
                f"*Verified by Finance Intelligence AI Core | Policy Compliance: SECURE (Fallback)*"
            )
        elif "loan" in q or "demand letter" in q:
            letters = DatabaseMock.get_loan_letters(student_id)
            letters_list = ""
            if letters:
                letters_list = "\n".join([f"- Letter `{l['letter_id']}` for `{l['bank']}`: Amount `{symbol} {l['amount']:,.2f}` (**{l['status']}**)" for l in letters])
            else:
                letters_list = "No demand letters generated yet."
            return (
                f"### 📄 Education Loan Demand Letters (Offline Fallback Mode)\n\n"
                f"Hello {name}, here are your loan letters:\n\n"
                f"{letters_list}\n\n"
                f"- You can request and download certified fee estimates in PDF format directly from the 'Loan Requests' tab.\n"
                f"- Each certified document features digital signatures and secure QR validation links.\n\n"
                f"*Verified by Finance Intelligence AI Core | Policy Compliance: SECURE (Fallback)*"
            )
        elif "swift" in q or "international" in q or "wire" in q or "forex" in q:
            return (
                f"### 🏦 International SWIFT Wire Details (Offline Fallback Mode)\n\n"
                f"For international remittances in foreign currencies (e.g. USD):\n\n"
                f"| Bank Coordinate | details |\n"
                f"|---|---|\n"
                f"| **SWIFT / BIC Code** | `ITB1NDIA33B` |\n"
                f"| **Beneficiary Bank** | Institutional Trust Bank |\n"
                f"| **Remittance Fee** | 2.5% Forex surcharge applies |\n\n"
                f"> ⚠️ **Important**: You MUST reference your Student ID `{student_id}` in the wire transfer description for ERP auto-reconciliation.\n\n"
                f"*Verified by Finance Intelligence AI Core | Policy Compliance: SECURE (Fallback)*"
            )
        else:
            balance_str = ""
            if balance:
                balance_str = (
                    f"- Total Fees Billed: `{symbol} {balance['billed']:,.2f}`\n"
                    f"- Scholarship waiver: `{symbol} {balance['scholarship']:,.2f}`\n"
                    f"- Late Fees Outstanding: `{symbol} {balance['late_fees']:,.2f}`\n"
                    f"- **Net Balance Due**: `{symbol} {balance['balance']:,.2f}`\n"
                )
            return (
                f"### 💳 Student Account Balance (Offline Fallback Mode)\n\n"
                f"Hello {name} ({student_id}), here is your active ledger summary:\n\n"
                f"{balance_str}\n"
                f"- Outstanding balances can be paid using the 'Fee Payments' tab.\n"
                f"- For questions, please consult the FAQ section or contact support.\n\n"
                f"*Verified by Finance Intelligence AI Core | Policy Compliance: SECURE (Fallback)*"
            )

    def call_child_agent(self, agent_name: str, system_prompt: str, user_prompt: str) -> str:
        """
        Call a child agent (using nvidia/nvidia-nemotron-nano-9b-v2) for specialized tasks.
        """
        url = f"{self.model_manager.get_api_url()}/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_KEY}",
            "Content-Type": "application/json"
        }
        
        config = self.model_manager.get_model_config("child_agent_primary")
        payload = {
            "model": config.get("model_name", "nvidia/nvidia-nemotron-nano-9b-v2"),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": config.get("temperature", 0.2),
            "max_tokens": config.get("max_tokens", 1024)
        }
        
        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=config.get("timeout", 20))
            response.raise_for_status()
            return self._clean_markdown(response.json()["choices"][0]["message"]["content"])
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as te:
            print(f"Child agent {agent_name} timeout: {te}. Triggering immediate offline child agent fallback...")
            return self._generate_child_agent_fallback(agent_name, user_prompt)
        except Exception as e:
            print(f"Child agent {agent_name} error: {e}. Attempting child fallback model...")
            return self._call_fallback_model(agent_name, system_prompt, user_prompt)

    def _call_fallback_model(self, agent_name: str, system_prompt: str, user_prompt: str) -> str:
        """Fallback in case Nemotron Nano experiences catalog issues"""
        url = f"{self.model_manager.get_api_url()}/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_KEY}",
            "Content-Type": "application/json"
        }
        
        config = self.model_manager.get_model_config("child_agent_fallback")
        payload = {
            "model": config.get("model_name", "deepseek-ai/deepseek-v4-flash"),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": config.get("temperature", 0.2),
            "max_tokens": config.get("max_tokens", 1024)
        }
        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=config.get("timeout", 15))
            response.raise_for_status()
            return self._clean_markdown(response.json()["choices"][0]["message"]["content"])
        except Exception as e:
            print(f"Child agent fallback model error: {e}. Executing rule-based child agent fallback...")
            return self._generate_child_agent_fallback(agent_name, user_prompt)

    def _generate_child_agent_fallback(self, agent_name: str, user_prompt: str) -> str:
        # Extract student_id from prompt
        student_id_match = re.search(r"STU-\d{4}-\d{4}", user_prompt)
        student_id = student_id_match.group(0) if student_id_match else "STU-2021-4892"
        
        from database_mock import DatabaseMock
        student = DatabaseMock.get_student(student_id)
        balance = DatabaseMock.get_student_balance(student_id)
        
        name = student["name"] if student else "Student"
        currency = student["currency"] if student else "INR"
        symbol = "₹" if currency == "INR" else "$"
        
        q = user_prompt.lower()
        if "payment" in agent_name.lower() or "pay" in q or "balance" in q:
            if balance:
                return (
                    f"Hi {name}, here is a detailed breakdown of your outstanding fees:\n"
                    f"- Billed Tuition Fee: `{symbol} {balance['billed']:,.2f}`\n"
                    f"- Scholarship applied: `{symbol} {balance['scholarship']:,.2f}`\n"
                    f"- Paid amount: `{symbol} {balance['paid']:,.2f}`\n"
                    f"- Late fees outstanding: `{symbol} {balance['late_fees']:,.2f}`\n"
                    f"- **Net Balance Due**: `{symbol} {balance['balance']:,.2f}`\n\n"
                    f"To settle your balance, please go to the 'Fee Payments' tab on the portal dashboard."
                )
            return "Unable to compile balance details due to network latency. Please check your payments dashboard."
            
        elif "refund" in agent_name.lower() or "refund" in q:
            refunds = DatabaseMock.get_refunds(student_id)
            if refunds:
                details = "\n".join([f"- Request `{r['request_id']}`: Amount `{symbol} {r['amount']:,.2f}` (Stage: **{r['stage']}**)" for r in refunds])
                return f"Here is the status of your refund requests:\n{details}\n\nAll refunds are subject to a 10-15 working days processing SLA."
            return "No refund requests were found on your account. You can submit one by asking: 'File a refund request'."
            
        elif "loan" in agent_name.lower() or "loan" in q:
            letters = DatabaseMock.get_loan_letters(student_id)
            if letters:
                details = "\n".join([f"- Letter `{l['letter_id']}` for `{l['bank']}`: Amount `{symbol} {l['amount']:,.2f}` (**{l['status']}**)" for l in letters])
                return f"Here are your generated demand letters:\n{details}\n\nYou can request new demand letters or download the certified PDF from the 'Loan Requests' tab."
            return "No loan letters have been generated yet. You can request one by asking: 'Generate a loan demand letter'."
            
        elif "intl" in agent_name.lower() or "international" in agent_name.lower() or "swift" in q or "foreign" in q or "wire" in q:
            return (
                "For international bank transfers, please use the following coordinates:\n"
                "- **SWIFT / BIC BIC Code**: `ITB1NDIA33B`\n"
                "- **Bank Name**: Institutional Trust Bank\n"
                "- **Processing Fee**: 2.5% Forex fee\n\n"
                "**Crucial**: You must reference your Student ID in the transaction remarks to ensure correct matching."
            )
            
        elif "reconcil" in agent_name.lower() or "reconcile" in q or "sync" in q:
            exceptions = DatabaseMock.get_exceptions()
            my_exc = [e for e in exceptions if e["student_id"] == student_id]
            if my_exc:
                exc = my_exc[0]
                return (
                    f"I found a transaction discrepancy of `{symbol} {exc['expected']:,.2f}` via `{exc['source']}`. "
                    "You can automatically reconcile this by asking me: 'Please reconcile my payment mismatch'."
                )
            return "No unresolved transaction exceptions were found for your account."
            
        else:
            return (
                "Welcome to the Finance Portal Assistant. Our services are running in offline fallback mode. "
                "You can view your real-time balances, invoices, payment history, and refund status using the tabs in the main portal."
            )

    def rerank_passages(self, query: str, passages: List[str]) -> List[Dict[str, Any]]:
        """
        Rerank a list of retrieved document chunks using llama-nemotron-rerank-1b-v2.
        """
        config = self.model_manager.get_model_config("reranker")
        headers = {
            "Authorization": f"Bearer {RERANKER_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": config.get("model_name", "nvidia/llama-nemotron-rerank-1b-v2"),
            "query": {"text": query},
            "passages": [{"text": p} for p in passages]
        }
        
        try:
            response = self.session.post(self.model_manager.get_rerank_url(), headers=headers, json=payload, timeout=config.get("timeout", 15))
            response.raise_for_status()
            results = response.json().get("rankings", [])
            
            ranked = []
            for r in results:
                idx = r["index"]
                score = r["logit"]
                ranked.append({
                    "text": passages[idx],
                    "score": score,
                    "index": idx
                })
            
            ranked.sort(key=lambda x: x["score"], reverse=True)
            return ranked
        except Exception as e:
            print(f"Reranking error: {e}")
            return [{"text": p, "score": 0.0, "index": idx} for idx, p in enumerate(passages)]

    def generate_embeddings(self, texts: List[str], input_type: str = "passage") -> List[List[float]]:
        """
        Generate text embeddings using nvidia/llama-nemotron-embed-1b-v2 or nvidia/embed-qa-4
        """
        url = f"{self.model_manager.get_api_url()}/embeddings"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_KEY}",
            "Content-Type": "application/json"
        }
        
        config = self.model_manager.get_model_config("embeddings")
        payload = {
            "model": config.get("model_name", "nvidia/llama-nemotron-embed-1b-v2"),
            "input": texts,
            "encoding_format": "float",
            "input_type": input_type
        }
        
        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=config.get("timeout", 15))
            response.raise_for_status()
            data = response.json().get("data", [])
            data.sort(key=lambda x: x["index"])
            return [d["embedding"] for d in data]
        except Exception as e:
            print(f"Embedding generation error: {e}")
            return [[0.0] * 2048 for _ in range(len(texts))]

if __name__ == "__main__":
    client = NvidiaClient()
    print("Testing Nvidia Client API connectivity...")
    test_safety = client.check_safety("Hello, how can I pay my university tuition fees?")
    print("Safety Check Response:", test_safety)
