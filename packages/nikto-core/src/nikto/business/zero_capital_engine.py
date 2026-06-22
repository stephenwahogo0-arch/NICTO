"""NIKTO Zero-Capital Business Engine — Start a real business with no money."""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class BusinessPlan:
    model_name: str
    capital_required: int
    currency: str
    steps: list
    first_week_actions: list
    action_plan: dict
    projections: dict
    free_tools: list
    time_to_first_revenue: str
    monthly_potential: str

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class NiktoZeroCapitalEngine:
    """
    NICTO's zero-capital business engine.
    Helps anyone start a real business with no money.

    Proven Zero-Capital Models:
    1. Service-first businesses (sell before you build)
    2. Digital product businesses (build once, sell forever)
    3. Arbitrage businesses (buy low sell high with credit)
    4. Platform businesses (connect buyers and sellers)
    5. Skill monetization (turn expertise into income)
    6. Agency model (resell others' services at markup)
    7. Affiliate and referral (earn from promoting others)
    8. Open source to business (build free, charge for services)
    9. Content to business (audience first, product second)
    10. B2B SaaS (build for businesses, charge subscription)
    """

    ZERO_CAPITAL_PLAYBOOKS = {
        "freelance_agency_nairobi": {
            "name": "Freelance Agency (Nairobi)",
            "capital_required": 0,
            "time_to_first_revenue": "7 days",
            "currency": "KES",
            "monthly_potential": "50,000 - 500,000 KES",
            "steps": [
                "Step 1: List your skills honestly. If you can code, design, write, or manage — that is your product.",
                "Step 2: Create profiles on Upwork, Fiverr, Toptal, and PeoplePerHour today. Free to join. Free to list services.",
                "Step 3: Set prices 20 percent below market to win first 5 clients. Get reviews. Then raise prices.",
                "Step 4: Deliver exceptional work. Ask every happy client for referrals. One referral beats 10 cold pitches.",
                "Step 5: After 5 clients, hire subcontractors on the same platforms to do the work. You manage. They deliver. You keep margin.",
                "Step 6: You are now an agency. No office needed. No capital needed. Just a laptop and internet.",
                "Step 7: Register business with Kenya Revenue Authority once you hit 50,000 KES/month. M-Pesa Paybill for payments. Free to set up.",
            ],
            "first_week_actions": [
                "Create Upwork profile with portfolio",
                "List 3 services on Fiverr",
                "Send 20 proposals on LinkedIn",
                "Join 5 Nairobi tech/business Facebook groups",
                "Post your services on Twitter/X",
                "Contact 10 local businesses offering your service",
                "Set up M-Pesa Paybill for payments",
            ],
            "tools_free": [
                "Canva (design)", "GitHub (code portfolio)", "Google Workspace free tier",
                "Zoom free tier", "Notion free tier", "Slack free tier", "Trello free tier",
            ],
        },
        "saas_zero_capital": {
            "name": "SaaS Product (Zero Capital)",
            "capital_required": 0,
            "time_to_first_revenue": "30-60 days",
            "currency": "KES/USD",
            "monthly_potential": "100,000 - 2,000,000 KES",
            "steps": [
                "Step 1: Find a painful problem in a market you understand. Pain = money. Talk to 20 people before building anything.",
                "Step 2: Build an MVP in 2 weeks using free tools. Next.js + Supabase free tier + Vercel free tier. Total cost: KES 0.",
                "Step 3: Pre-sell before launch. Find 10 people willing to pay for the solution. Take M-Pesa deposits. If nobody pays — the idea is wrong. Pivot. No money lost.",
                "Step 4: Build only what the paying customers asked for. Ship in 2-week sprints. Get feedback. Improve.",
                "Step 5: Use Stripe for international payments. Use Pesapal or IntaSend for Kenya payments. Both free to sign up. Pay per transaction.",
                "Step 6: Content marketing is free. Write about the problem you solve. Post on LinkedIn, Twitter, dev.to. SEO takes 3-6 months but costs nothing.",
                "Step 7: When revenue covers hosting costs — you are profitable. Scale from there.",
            ],
            "free_hosting_stack": [
                "Vercel (frontend + serverless — free tier)", "Supabase (database + auth — free tier)",
                "Railway (backend — free tier)", "Cloudflare (CDN + DNS — free)",
                "GitHub (code + CI/CD — free)", "PlanetScale (MySQL — free tier)", "Upstash (Redis — free tier)",
            ],
            "monetization_models": [
                "Freemium: free basic, paid advanced", "Per-seat: charge per user per month",
                "Usage-based: charge per API call or action", "One-time purchase: pay once, use forever",
                "Lifetime deal: AppSumo launch for early cash",
            ],
        },
        "ai_consulting_nairobi": {
            "name": "AI Consulting Business (Nairobi)",
            "capital_required": 0,
            "time_to_first_revenue": "14 days",
            "currency": "KES",
            "monthly_potential": "150,000 - 1,500,000 KES",
            "steps": [
                "Step 1: Package your AI knowledge into services. Service 1: AI chatbot setup (KES 50,000). Service 2: AI automation audit (KES 30,000). Service 3: Monthly AI maintenance retainer (KES 20,000/mo).",
                "Step 2: Target businesses in Nairobi wasting money on manual processes. Banks, hospitals, schools, hotels, SACCOs. Any business with repetitive staff tasks.",
                "Step 3: Offer a free 30-minute audit call. Show them exactly how much they are losing to manual processes. Then quote your solution.",
                "Step 4: Use NICTO to build the solutions faster. What takes others 2 weeks, you do in 3 days. Your margin is your speed.",
                "Step 5: Deliver. Get testimonial. Use testimonial to get next client. Repeat until you have 5 recurring retainers.",
                "Step 6: Hire junior developers to deliver. You sell. They build. You scale.",
            ],
            "target_clients_nairobi": [
                "SACCOs needing member management automation", "Schools needing fee tracking and reporting",
                "Restaurants needing ordering and inventory systems", "Clinics needing patient records and booking",
                "Real estate agents needing listing management", "Import/export businesses needing tracking systems",
                "NGOs needing donor management systems",
            ],
            "proposal_template": "Subject: How [Company Name] Can Save [X] Hours Per Week\n\nDear [Name],\n\nI analyzed [Company Name]'s operations and identified 3 processes that AI can automate immediately...\n\nI can implement these solutions within 2 weeks.\nInvestment: KES [Amount] (one-time setup)\nMonthly retainer: KES [Amount] (maintenance and improvements)\n\nStephen Wahogo\nNICTO AI Solutions | Nairobi, Kenya",
        },
        "bug_bounty_income": {
            "name": "Bug Bounty Income Stream",
            "capital_required": 0,
            "time_to_first_revenue": "30 days",
            "currency": "USD",
            "monthly_potential": "500 - 50,000 USD",
            "steps": [
                "Step 1: Register on HackerOne, Bugcrowd, and Intigriti today. Free to join.",
                "Step 2: Start with programs that have 'VRT:Informational' to 'VRT:Medium' bugs. Lower competition. Faster payouts.",
                "Step 3: Use NICTO's security scanner to automate initial reconnaissance. NICTO runs nmap, subfinder, nuclei while you sleep.",
                "Step 4: Focus on one bug class at first. Learn IDOR deeply. Or XSS deeply. Master one before spreading out.",
                "Step 5: Document everything meticulously. Clear PoC. Video proof. Professional reports get paid faster.",
                "Step 6: Reinvest first bounty into VPN and better tools. Everything else is profit.",
            ],
            "top_bug_classes": [
                "IDOR (Insecure Direct Object References)", "Broken authentication",
                "Information disclosure", "CSRF (Cross-Site Request Forgery)",
                "Open redirects", "Subdomain takeover",
                "Missing security headers", "Rate limiting bypass",
            ],
        },
        "open_source_to_business": {
            "name": "Open Source to Business",
            "capital_required": 0,
            "time_to_first_revenue": "90 days",
            "currency": "USD",
            "monthly_potential": "1,000 - 100,000 USD",
            "steps": [
                "Step 1: Build something genuinely useful. Put it on GitHub. Make it excellent. Not a tutorial project. A real tool.",
                "Step 2: Market it like a product. README with clear value proposition. Demo GIF. Post on HackerNews, Reddit r/programming, ProductHunt.",
                "Step 3: When you hit 500 GitHub stars — you have proof of market demand. Now build the paid tier.",
                "Step 4: Open core model: Free self-hosted version. Paid cloud-hosted version. Enterprise support contracts.",
                "Step 5: GitHub Sponsors. Once you have users, some will pay to keep you building. Set up sponsor tiers.",
                "Step 6: Consulting around your own tool. Companies will pay you to install, configure, and customize it for them.",
            ],
        },
        "digital_products": {
            "name": "Digital Products Business",
            "capital_required": 0,
            "time_to_first_revenue": "14 days",
            "currency": "USD/KES",
            "monthly_potential": "30,000 - 500,000 KES",
            "digital_products_to_build": [
                "Security checklists and pentesting templates (KES 2,000)", "Code snippets and component libraries (KES 5,000)",
                "Figma UI kits (KES 3,000)", "Video courses on platforms (Udemy/Gumroad)",
                "eBooks on technical topics", "Notion templates for developers",
                "GitHub Actions workflow templates", "Prompt engineering guides",
                "CTF writeup collections", "Network diagram templates",
            ],
            "selling_platforms_free": [
                "Gumroad (0 monthly fee, takes %, free to start)", "Lemon Squeezy (free to start)",
                "Payhip (free tier available)", "Ko-fi (free tier)",
                "Selar.co (Kenya-focused, free to start)", "Udemy (free to publish)",
            ],
        },
    }

    def __init__(self, brain):
        self.brain = brain
        self.active_businesses = []
        self.revenue_generated = 0.0

    async def start_business(self, model_name: str, user_skills: list,
                             location: str = "Nairobi, Kenya",
                             time_available_hours_per_week: int = 20) -> BusinessPlan:
        if model_name not in self.ZERO_CAPITAL_PLAYBOOKS:
            model_name = self._recommend_model(user_skills)
        playbook = self.ZERO_CAPITAL_PLAYBOOKS[model_name]
        customized_steps = await self._customize_steps(playbook["steps"], user_skills, location, time_available_hours_per_week)
        action_plan = await self._generate_action_plan(playbook, user_skills, time_available_hours_per_week)
        projections = await self._generate_projections(playbook, time_available_hours_per_week)
        return BusinessPlan(
            model_name=model_name, capital_required=0,
            currency=playbook.get("currency", "KES"), steps=customized_steps,
            first_week_actions=playbook.get("first_week_actions", []),
            action_plan=action_plan, projections=projections,
            free_tools=playbook.get("tools_free", []),
            time_to_first_revenue=playbook.get("time_to_first_revenue", "30 days"),
            monthly_potential=playbook.get("monthly_potential", "Unknown"),
        )

    def _recommend_model(self, user_skills: list) -> str:
        skills_lower = [s.lower() for s in user_skills]
        if any(k in skills_lower for k in ["python", "javascript", "coding", "programming"]):
            return "saas_zero_capital"
        elif any(k in skills_lower for k in ["security", "hacking", "pentesting", "ctf"]):
            return "bug_bounty_income"
        elif any(k in skills_lower for k in ["ai", "machine learning", "nlp"]):
            return "ai_consulting_nairobi"
        elif any(k in skills_lower for k in ["open source", "github", "tools"]):
            return "open_source_to_business"
        else:
            return "freelance_agency_nairobi"

    async def _customize_steps(self, steps, skills, location, hours) -> list:
        return steps

    async def _generate_action_plan(self, playbook, skills, hours) -> dict:
        return {
            "week_1": playbook.get("first_week_actions", []),
            "week_2": ["Focus on first client acquisition"],
            "week_3": ["Deliver first project"],
            "week_4": ["Get testimonial, start client 2"],
            "month_2": ["Scale to 3 paying clients"],
            "month_3": ["Hire first subcontractor"],
            "month_6": ["Registered business, 5 clients"],
        }

    async def _generate_projections(self, playbook, hours) -> dict:
        return {
            "month_1": {"revenue_kes": 15000, "expenses_kes": 0, "profit_kes": 15000},
            "month_3": {"revenue_kes": 75000, "expenses_kes": 5000, "profit_kes": 70000},
            "month_6": {"revenue_kes": 200000, "expenses_kes": 30000, "profit_kes": 170000},
            "month_12": {"revenue_kes": 500000, "expenses_kes": 100000, "profit_kes": 400000},
        }

    async def list_models(self) -> list:
        return [{"name": name, "capital": data["capital_required"],
                  "time_to_revenue": data["time_to_first_revenue"],
                  "monthly_potential": data["monthly_potential"]}
                for name, data in self.ZERO_CAPITAL_PLAYBOOKS.items()]

    def save(self) -> dict:
        return {"active_businesses": self.active_businesses, "revenue_generated": self.revenue_generated}

    def load(self, data: dict):
        self.active_businesses = data.get("active_businesses", [])
        self.revenue_generated = data.get("revenue_generated", 0.0)
