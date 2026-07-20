#!/usr/bin/env python3
"""Run fixed Green Spectrum MVP dummy-company tests.

This is intentionally deterministic and API-free. It exercises the local
backend analysis/persistence functions, then writes spreadsheet-ready outputs.
"""

from __future__ import annotations

import csv
import json
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path

import server


OUTPUT_DIR = Path("outputs")
DETAILED_DIR = OUTPUT_DIR / "green_spectrum_google_sheets_tabs"
RESULTS_CSV = OUTPUT_DIR / "green_spectrum_dummy_test_results.csv"
RESULTS_JSON = OUTPUT_DIR / "green_spectrum_dummy_test_runs.json"
GOOGLE_SHEETS_NOTE = OUTPUT_DIR / "google_sheets_import_README.md"


FIXTURES = [
    {
        "id": "northforge",
        "company": "Northforge Components Ltd",
        "sector": "Advanced manufacturing",
        "size": "850 employees",
        "revenue": "GBP 100m-250m",
        "regions": "UK, Germany, Poland",
        "products": "Precision metal components for automotive, aerospace and industrial customers",
        "maturity": "developing",
        "data_richness": "medium",
        "contradiction_level": "low",
        "missing_field_level": "medium",
        "regulation": "medium",
        "goal": "Identify where to focus carbon-reduction activity",
        "barriers": ["Cost-led procurement", "Incomplete supplier data", "Certification constraints", "Small sustainability team"],
        "business": "Customer cost pressure, energy volatility, strict certification and growing carbon-data requirements shape decisions.",
        "human": "Factory workers, engineers, procurement teams, suppliers and upstream communities are affected; procurement and customers hold most power.",
        "planetary": "Purchased steel and aluminium, electricity, natural gas, lubricants and freight dominate impacts; supplier-specific evidence is weak.",
        "journey": [
            ["Raw materials", "Steel and aluminium production", "High embodied carbon and mining impacts", "Metal suppliers, mining communities", "low", "low"],
            ["Supplier selection", "Supplier contracting", "Material source and data quality", "Procurement, suppliers", "medium", "medium"],
            ["Transport", "European freight", "Fuel use and emissions", "Logistics providers", "medium", "low"],
            ["Manufacturing", "Machining and heat processes", "Energy use, scrap and lubricants", "Operations, workers", "high", "high"],
            ["Quality control", "Testing and certification", "Material substitution constraints", "Engineers, customers", "high", "high"],
            ["Customer use", "Components in machinery", "Efficiency implications", "Customers", "low", "low"],
            ["End of life", "Metal recycling", "Recovery potential", "Recyclers, customers", "low", "medium"],
        ],
        "challenges": [
            ["Purchased-metal emissions", 5, 4, 5, 4, 3, 2, 3, 4, 5, 3, "Materials and suppliers"],
            ["Factory energy efficiency", 3, 4, 4, 2, 5, 5, 4, 3, 3, 2, "Operations"],
            ["Employee engagement", 2, 2, 3, 3, 4, 3, 4, 2, 3, 2, "People"],
            ["Supplier data quality", 4, 4, 5, 3, 3, 2, 2, 3, 5, 2, "Evidence"],
            ["Product redesign constraints", 4, 3, 4, 2, 3, 3, 2, 5, 4, 3, "Innovation"],
        ],
        "prototype": {
            "priority": "Purchased-metal emissions",
            "hypothesis": "A low-carbon aluminium supplier can reduce embodied emissions without unacceptable cost or quality impacts.",
            "intervention": "Test one low-carbon aluminium specification on a limited product batch.",
            "owner": "Head of Engineering",
            "participants": ["Procurement", "Quality", "Sustainability", "Supplier"],
            "metric": "Product carbon estimate, defect rate, unit cost and lead time",
            "success": "At least 25 percent embodied-carbon reduction with less than 5 percent cost increase and no quality failure",
            "risk": "Certification or quality failure",
            "expected": "Supplier and material evidence",
        },
    },
    {
        "id": "lumathread",
        "company": "LumaThread Apparel",
        "sector": "Fashion and apparel",
        "size": "1,400 employees",
        "revenue": "GBP 250m-500m",
        "regions": "UK, Turkey, Bangladesh, Vietnam",
        "products": "Mid-market clothing and accessories",
        "maturity": "developing",
        "data_richness": "medium",
        "contradiction_level": "high",
        "missing_field_level": "high",
        "regulation": "medium",
        "goal": "Improve traceability and reduce environmental and labour risk",
        "barriers": ["Fast product cycles", "Weak traceability", "Supplier fear", "Unsupported claims risk"],
        "business": "Brand, speed and affordability create value, but overproduction, returns and claim risk threaten reputation.",
        "human": "Factory workers have low power while buyers create pressure; customers want affordability and sustainability together.",
        "planetary": "Cotton, polyester, dyeing, air freight, short garment life and weak recycling create broad lifecycle impacts.",
        "journey": [
            ["Fibre production", "Cotton and synthetic fibre sourcing", "Water, land and fossil materials", "Farmers, fibre suppliers", "low", "low"],
            ["Textile processing", "Dyeing and finishing", "Chemical, water and energy impacts", "Mills, workers", "medium", "low"],
            ["Garment manufacturing", "Cut-make-trim production", "Labour conditions and wages", "Factory workers, suppliers", "medium", "medium"],
            ["Buying and planning", "Collection planning", "Overproduction and supplier pressure", "Buyers, designers", "high", "medium"],
            ["Transport", "Freight recovery", "Air freight emissions", "Logistics teams", "medium", "low"],
            ["Retail and returns", "Sales and reverse logistics", "Packaging, unsold goods and returns", "Customers, stores", "high", "medium"],
            ["Use and end of life", "Washing and disposal", "Durability and poor recycling", "Customers, recyclers", "low", "low"],
        ],
        "challenges": [
            ["Supply-chain traceability", 5, 5, 5, 5, 3, 2, 2, 4, 5, 4, "Traceability"],
            ["Labour conditions", 5, 4, 5, 5, 2, 2, 2, 4, 5, 4, "People"],
            ["Overproduction and returns", 4, 4, 4, 4, 5, 3, 3, 3, 4, 3, "Commercial model"],
            ["Unsupported claims", 4, 5, 5, 4, 5, 2, 3, 2, 4, 4, "Governance"],
            ["Material selection", 4, 3, 4, 3, 4, 2, 3, 3, 4, 3, "Materials"],
        ],
        "prototype": {
            "priority": "Supply-chain traceability",
            "hypothesis": "Verified material-impact information will improve sourcing decisions without delaying the product cycle.",
            "intervention": "Apply a Green Spectrum material-decision canvas to one seasonal collection.",
            "owner": "Head of Buying",
            "participants": ["Design", "Buying", "Sustainability", "Two suppliers"],
            "metric": "Traceable source percentage, decision time, material cost, estimated impact and user confidence",
            "success": "Improved traceability and sourcing confidence without collection delay",
            "risk": "Teams avoid use because it slows buying decisions",
            "expected": "Traceability, labour and claims",
        },
    },
    {
        "id": "evergreen",
        "company": "Evergreen Bank",
        "sector": "Financial services",
        "size": "4,800 employees",
        "revenue": "GBP 1bn-2bn",
        "regions": "UK and Ireland",
        "products": "Mortgages, business loans and investments",
        "maturity": "advanced reporting, medium implementation",
        "data_richness": "high",
        "contradiction_level": "medium",
        "missing_field_level": "medium",
        "regulation": "high",
        "goal": "Integrate sustainability into lending decisions",
        "barriers": ["Customer data gaps", "Fairness concerns", "Regulatory scrutiny", "Relationship-manager capability"],
        "business": "Lending, investment and risk management create value; financed emissions dwarf office impacts.",
        "human": "Lending criteria affect households and SMEs; strict green rules could exclude lower-income customers.",
        "planetary": "Capital allocation is the main leverage point, with property energy, flood risk and business-sector impacts.",
        "journey": [
            ["Product design", "Lending criteria", "Transition finance and exclusion risk", "Product, risk, customers", "high", "high"],
            ["Customer assessment", "Data request and affordability review", "Fairness and evidence burden", "Relationship managers, SMEs", "high", "medium"],
            ["Credit decision", "Capital allocation", "Financed emissions and risk", "Credit committee", "high", "high"],
            ["Loan conditions", "Covenants and support", "Transition support quality", "Customers, legal", "medium", "medium"],
            ["Monitoring", "Progress and data review", "Data quality and accountability", "Risk, customers", "medium", "medium"],
            ["Renewal", "Terms adjustment", "Opportunity to improve terms", "Customers", "medium", "medium"],
            ["Reporting", "Regulatory disclosure", "Investor and regulatory scrutiny", "Regulators, investors", "high", "high"],
        ],
        "challenges": [
            ["Financed emissions evidence", 5, 4, 5, 4, 3, 2, 3, 4, 5, 3, "Evidence"],
            ["Climate-risk integration", 5, 5, 5, 4, 4, 4, 4, 3, 5, 3, "Risk"],
            ["Fairness of green lending criteria", 4, 4, 5, 5, 4, 3, 3, 3, 4, 4, "People"],
            ["Relationship-manager capability", 3, 4, 4, 4, 5, 3, 4, 2, 3, 2, "Capability"],
            ["Nature-related exposure", 4, 3, 4, 3, 2, 1, 2, 4, 4, 4, "Nature"],
        ],
        "prototype": {
            "priority": "Climate-risk integration",
            "hypothesis": "A sustainability decision prompt during SME loan review improves climate-risk consideration without unfair exclusion.",
            "intervention": "Pilot a decision prompt in SME loan review.",
            "owner": "Head of Credit Risk",
            "participants": ["Relationship managers", "Credit risk", "Sustainability", "Compliance"],
            "metric": "Completion rate, decision time, evidence quality, approval outcomes, fairness concerns and user confidence",
            "success": "Improved sustainability evidence with no adverse fairness pattern",
            "risk": "Prompt becomes a compliance tick-box or creates exclusion bias",
            "expected": "Finance and lending decisions",
        },
    },
    {
        "id": "civiccare",
        "company": "CivicCare Health Trust",
        "sector": "Healthcare",
        "size": "12,000 employees",
        "revenue": "GBP 1bn-2bn annual budget",
        "regions": "Five hospitals and 42 community locations",
        "products": "Healthcare services",
        "maturity": "uneven",
        "data_richness": "medium",
        "contradiction_level": "medium",
        "missing_field_level": "medium",
        "regulation": "high",
        "goal": "Reduce environmental impact without compromising patient care",
        "barriers": ["Clinical governance", "Capital constraints", "Staff fatigue", "Procurement rules"],
        "business": "Safe healthcare is the primary value; budgets, clinical regulation and ageing infrastructure constrain change.",
        "human": "Patients and vulnerable groups are central; clinicians hold strong authority and staff are fatigued.",
        "planetary": "Energy, medicines, anaesthetic gases, clinical products, waste, transport and procurement dominate impacts.",
        "journey": [
            ["Procurement", "Medicines, devices and consumables", "Upstream product impacts", "Procurement, clinicians", "medium", "medium"],
            ["Patient travel", "Access to care", "Transport emissions and equity", "Patients, communities", "medium", "medium"],
            ["Clinical treatment", "Anaesthetic gases and single-use items", "High climate impact and safety constraints", "Clinicians, patients", "high", "medium"],
            ["Facilities", "Heat, electricity and water", "Energy and water impacts", "Estates, patients", "high", "high"],
            ["Waste", "Clinical disposal", "Hazardous waste", "Waste contractors, staff", "medium", "medium"],
            ["Community services", "Decentralised care", "Travel and access trade-offs", "Patients, staff", "medium", "medium"],
            ["Supplier management", "Evidence requests", "Upstream evidence quality", "Suppliers", "low", "low"],
        ],
        "challenges": [
            ["Anaesthetic gases", 5, 5, 5, 4, 5, 4, 4, 3, 5, 3, "Clinical impact"],
            ["Hospital energy", 4, 4, 4, 3, 5, 5, 3, 4, 4, 2, "Facilities"],
            ["Sustainable procurement", 4, 4, 4, 3, 3, 2, 2, 4, 5, 4, "Procurement"],
            ["Clinical waste", 3, 3, 4, 3, 4, 3, 3, 3, 3, 3, "Waste"],
            ["Patient and staff travel", 3, 3, 3, 5, 3, 3, 3, 4, 4, 3, "People"],
        ],
        "prototype": {
            "priority": "Anaesthetic gases",
            "hypothesis": "Anaesthetic-impact feedback will reduce high-impact gas use without affecting patient outcomes.",
            "intervention": "Provide clinicians with anaesthetic-impact feedback in one theatre group.",
            "owner": "Clinical Sustainability Lead",
            "participants": ["Anaesthetists", "Clinical governance", "Estates", "Sustainability"],
            "metric": "Gas use, clinical outcomes, clinician acceptance, cost and emissions estimate",
            "success": "Reduced high-impact gas use with no patient safety issue",
            "risk": "Clinical safety or acceptance concern",
            "expected": "Clinically safe emissions intervention",
        },
    },
    {
        "id": "terrabite",
        "company": "TerraBite Foods",
        "sector": "Food manufacturing and agriculture",
        "size": "2,300 employees",
        "revenue": "GBP 500m-1bn",
        "regions": "UK, Spain, Kenya, Brazil",
        "products": "Food products from agricultural ingredients",
        "maturity": "strong carbon focus, weak nature integration",
        "data_richness": "medium",
        "contradiction_level": "low",
        "missing_field_level": "high",
        "regulation": "medium",
        "goal": "Improve agricultural resilience and reduce nature impacts",
        "barriers": ["Supplier bargaining power", "Water stress", "Deforestation risk", "Retail cost pressure"],
        "business": "Affordable, reliable ingredients create value; climate and ingredient volatility threaten continuity.",
        "human": "Farmers may have low bargaining power and transition costs may fall on suppliers.",
        "planetary": "Farming dominates carbon, water and biodiversity impacts; fertiliser, water stress and soil health matter.",
        "journey": [
            ["Farming", "Ingredient production", "Soil, water, fertiliser and biodiversity", "Farmers, communities", "low", "medium"],
            ["Aggregation", "Ingredient aggregation", "Loss of traceability", "Aggregators, suppliers", "medium", "low"],
            ["Processing", "Food manufacturing", "Energy, water and food loss", "Factory workers", "high", "medium"],
            ["Packaging", "Pack selection", "Plastic and board impacts", "Packaging suppliers", "medium", "high"],
            ["Distribution", "Cold chain", "Refrigeration and transport", "Logistics", "medium", "medium"],
            ["Retail", "Specifications", "Waste and buyer influence", "Retailers", "low", "medium"],
            ["Consumption", "Use and disposal", "Nutrition and food waste", "Consumers", "low", "low"],
        ],
        "challenges": [
            ["Farm water and soil resilience", 5, 4, 5, 5, 2, 2, 2, 4, 5, 4, "Nature"],
            ["Fertiliser dependency", 4, 4, 4, 3, 3, 3, 3, 3, 4, 3, "Agriculture"],
            ["Deforestation traceability", 5, 4, 5, 4, 2, 1, 2, 4, 5, 4, "Traceability"],
            ["Processing water efficiency", 3, 3, 3, 2, 5, 4, 4, 2, 3, 2, "Operations"],
            ["Packaging visibility bias", 2, 3, 3, 3, 4, 5, 5, 2, 2, 2, "Packaging"],
        ],
        "prototype": {
            "priority": "Farm water and soil resilience",
            "hypothesis": "Supporting a small supplier group with soil-health practices improves resilience and reduces fertiliser dependency.",
            "intervention": "Pilot soil-health practice support with one supplier group.",
            "owner": "Agricultural Supply Lead",
            "participants": ["Farmers", "Procurement", "Agronomist", "Sustainability"],
            "metric": "Fertiliser use, yield, soil indicators, farmer cost, farmer income and water use",
            "success": "Improved resilience indicators without reducing farmer income",
            "risk": "Supplier burden or low evidence quality",
            "expected": "Farm, water and nature resilience",
        },
    },
    {
        "id": "urbanrise",
        "company": "UrbanRise Developments",
        "sector": "Construction and property development",
        "size": "600 employees",
        "revenue": "GBP 250m-500m",
        "regions": "UK regional development projects",
        "products": "Residential and mixed-use developments",
        "maturity": "inconsistent between projects",
        "data_richness": "medium",
        "contradiction_level": "medium",
        "missing_field_level": "medium",
        "regulation": "high",
        "goal": "Reduce embodied carbon and improve community value",
        "barriers": ["Planning risk", "Contractor resistance", "Early design lock-in", "Affordable housing cost pressure"],
        "business": "Project viability depends on cost, planning and delivery time; design decisions lock in impacts early.",
        "human": "Communities, future occupants and workers experience project decisions, but community voices often arrive late.",
        "planetary": "Concrete, steel, site selection, operational energy, waste and end-of-life adaptability drive impacts.",
        "journey": [
            ["Site acquisition", "Land selection", "Land and ecosystem impact", "Land owners, communities", "medium", "medium"],
            ["Concept design", "Early design choices", "Highest decision leverage", "Designers, investors", "high", "medium"],
            ["Planning", "Approval process", "Community and regulatory approval", "Authorities, communities", "medium", "medium"],
            ["Detailed design", "Materials and performance", "Embodied and operational carbon", "Architects, engineers", "high", "medium"],
            ["Procurement", "Contractor selection", "Specification delivery", "Contractors", "medium", "medium"],
            ["Construction", "Site works", "Waste, transport and safety", "Workers, neighbours", "medium", "medium"],
            ["Use", "Building occupation", "Energy, water and wellbeing", "Occupants", "low", "low"],
            ["End of life", "Adaptability and demolition", "Reuse and waste", "Future owners", "low", "low"],
        ],
        "challenges": [
            ["Early design carbon lock-in", 5, 4, 5, 4, 5, 3, 3, 3, 5, 3, "Design"],
            ["Community trust and planning", 4, 5, 5, 5, 4, 3, 3, 3, 4, 4, "People"],
            ["Low-carbon material adoption", 4, 4, 4, 3, 4, 3, 3, 4, 4, 3, "Materials"],
            ["Construction waste", 3, 3, 3, 2, 4, 4, 4, 2, 3, 2, "Waste"],
            ["Biodiversity on sites", 4, 3, 4, 4, 3, 2, 3, 3, 4, 3, "Nature"],
        ],
        "prototype": {
            "priority": "Early design carbon lock-in",
            "hypothesis": "A carbon and social-value checkpoint during concept design improves outcomes without unacceptable delay.",
            "intervention": "Add a concept-design decision checkpoint on one live project.",
            "owner": "Design Director",
            "participants": ["Design", "Commercial", "Planning", "Community engagement"],
            "metric": "Embodied-carbon estimate, design changes, project cost, planning risk, decision time and stakeholder concerns",
            "success": "Better design decisions without material planning delay",
            "risk": "Checkpoint is bypassed because of programme pressure",
            "expected": "Early-stage design leverage",
        },
    },
    {
        "id": "cloudspring",
        "company": "CloudSpring Technologies",
        "sector": "Software and cloud services",
        "size": "1,100 employees",
        "revenue": "GBP 250m-500m",
        "regions": "Remote-first",
        "products": "Cloud software and AI-enabled digital services",
        "maturity": "early",
        "data_richness": "low",
        "contradiction_level": "low",
        "missing_field_level": "high",
        "regulation": "low",
        "goal": "Understand environmental impact of digital products",
        "barriers": ["Cloud data dependency", "Assumption of low impact", "AI workload growth", "Claim uncertainty"],
        "business": "Growth depends on computing capacity; AI increases cost and energy demand while customers ask for evidence.",
        "human": "Engineers influence architecture; sales need claim guidance and customers cannot easily see product footprint.",
        "planetary": "Indirect electricity, data-centre water, hardware, AI workloads, e-waste and efficient software are central.",
        "journey": [
            ["Product design", "Feature and architecture choices", "Computational demand", "Engineers, product", "high", "low"],
            ["Cloud procurement", "Provider selection", "Energy and water dependency", "Cloud suppliers", "medium", "low"],
            ["Development", "Testing and hardware", "Hardware and testing impacts", "Developers", "high", "medium"],
            ["Deployment", "Data storage and processing", "Ongoing compute demand", "DevOps, customers", "high", "low"],
            ["Customer use", "Product use", "Customer resource use", "Customers", "medium", "low"],
            ["Employee work", "Remote work", "Travel and home energy", "Employees", "low", "low"],
            ["End of life", "Devices and data retention", "E-waste and storage", "IT, suppliers", "medium", "low"],
        ],
        "challenges": [
            ["Cloud impact evidence", 5, 4, 5, 3, 3, 1, 2, 3, 5, 3, "Evidence"],
            ["AI workload growth", 4, 4, 5, 3, 5, 2, 3, 3, 4, 3, "Digital impact"],
            ["Engineering efficiency behaviour", 3, 3, 4, 3, 5, 2, 4, 2, 4, 2, "People"],
            ["Customer environmental claims", 3, 4, 4, 4, 4, 1, 3, 2, 3, 3, "Claims"],
            ["Hardware lifecycle", 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, "Hardware"],
        ],
        "prototype": {
            "priority": "Cloud impact evidence",
            "hypothesis": "Showing compute-cost and estimated energy information during development reduces unnecessary resource use.",
            "intervention": "Add compute and estimated energy feedback to one engineering team workflow.",
            "owner": "Platform Engineering Lead",
            "participants": ["Engineering", "Product", "Cloud procurement", "Sustainability"],
            "metric": "Compute hours, storage, response time, cost, estimated energy and developer usability",
            "success": "Reduced avoidable compute with no product performance harm",
            "risk": "Energy estimates are too uncertain to guide decisions",
            "expected": "Digital and cloud impact evidence",
        },
    },
    {
        "id": "loophome",
        "company": "LoopHome Circular Services",
        "sector": "Circular consumer services",
        "size": "75 employees",
        "revenue": "GBP 5m-10m",
        "regions": "UK",
        "products": "Subscription-based refurbished appliances",
        "maturity": "high ambition, low formal maturity",
        "data_richness": "low",
        "contradiction_level": "medium",
        "missing_field_level": "high",
        "regulation": "low",
        "goal": "Verify whether the circular business model creates genuine environmental benefit",
        "barriers": ["Reverse logistics cost", "Weak impact evidence", "Rebound effects", "Growth pressure"],
        "business": "Profit depends on repair cost, lifetime and retention; investors expect rapid growth and impact evidence.",
        "human": "Repair technicians are overloaded, customers value convenience and investors influence expansion speed.",
        "planetary": "Reuse may avoid new manufacturing, but older appliance energy, logistics and rebound effects may undermine benefit.",
        "journey": [
            ["Product acquisition", "Sourcing used appliances", "Quality uncertainty", "Customers, suppliers", "medium", "low"],
            ["Inspection", "Screening products", "Product rejection", "Technicians", "high", "medium"],
            ["Repair", "Repair workflow", "Labour, energy and parts", "Technicians", "high", "medium"],
            ["Delivery", "Reverse logistics", "Transport emissions", "Drivers, customers", "medium", "medium"],
            ["Customer use", "Subscription use", "Appliance efficiency and behaviour", "Customers", "low", "low"],
            ["Return", "Churn and replacement", "Transport and replacement impacts", "Customers, drivers", "medium", "low"],
            ["End of life", "Parts recovery", "Recycling and disposal", "Recyclers", "medium", "low"],
        ],
        "challenges": [
            ["Validate circular impact", 5, 4, 5, 4, 3, 1, 2, 3, 5, 4, "Circularity"],
            ["Customer churn and transport", 4, 4, 4, 4, 4, 2, 3, 2, 4, 3, "Behaviour"],
            ["Technician capacity", 3, 4, 4, 4, 4, 3, 3, 3, 3, 2, "People"],
            ["Appliance energy performance", 4, 3, 4, 3, 2, 2, 2, 3, 4, 3, "Product use"],
            ["Investor growth pressure", 3, 3, 4, 3, 3, 2, 3, 2, 3, 3, "Business model"],
        ],
        "prototype": {
            "priority": "Validate circular impact",
            "hypothesis": "Extending the minimum customer subscription period reduces transport and replacement impacts without excessive customer loss.",
            "intervention": "Test a longer minimum subscription period with one customer segment.",
            "owner": "Customer Operations Lead",
            "participants": ["Customer operations", "Repair", "Logistics", "Finance"],
            "metric": "Churn, product lifetime, transport journeys, satisfaction, profitability and estimated avoided manufacturing",
            "success": "Lower transport and replacement impact without unacceptable churn",
            "risk": "Customer dissatisfaction or reduced accessibility",
            "expected": "Validate circular impact",
        },
    },
    {
        "id": "citymotion",
        "company": "CityMotion Transit Authority",
        "sector": "Public transport",
        "size": "7,500 employees",
        "revenue": "GBP 2bn-3bn annual budget",
        "regions": "Metropolitan transport network",
        "products": "Public bus and transit services",
        "maturity": "strong planning, slow execution",
        "data_richness": "high",
        "contradiction_level": "medium",
        "missing_field_level": "low",
        "regulation": "high",
        "goal": "Develop a fair low-carbon fleet transition",
        "barriers": ["Capital investment", "Procurement cycles", "Maintenance capability", "Political scrutiny"],
        "business": "Reliability, affordability and ridership create public value; fleet changes need large capital and long procurement.",
        "human": "Passengers include vulnerable groups; drivers, technicians, unions and communities are strongly affected.",
        "planetary": "Diesel emissions, battery supply chains, infrastructure, air quality, flooding and heat resilience are central.",
        "journey": [
            ["Network planning", "Route and service planning", "Accessibility and equity", "Passengers, communities", "high", "high"],
            ["Vehicle procurement", "Fleet choices", "Lifecycle impact", "Procurement, suppliers", "medium", "medium"],
            ["Infrastructure", "Depots and charging", "Embodied carbon and readiness", "Infrastructure teams", "medium", "medium"],
            ["Operations", "Fuel and service delivery", "Direct emissions and reliability", "Drivers, passengers", "high", "high"],
            ["Passenger use", "Mode shift", "Public value and emissions", "Passengers", "medium", "high"],
            ["Maintenance", "Skills and parts", "Capability constraint", "Technicians, unions", "high", "high"],
            ["End of life", "Vehicles and batteries", "Battery and vehicle disposal", "Suppliers, recyclers", "medium", "medium"],
        ],
        "challenges": [
            ["Fair fleet transition", 5, 5, 5, 5, 4, 4, 3, 4, 5, 4, "Fleet"],
            ["Accessibility safeguard", 5, 5, 5, 5, 5, 4, 4, 3, 4, 3, "People"],
            ["Charging infrastructure readiness", 4, 5, 5, 3, 3, 3, 2, 4, 5, 3, "Infrastructure"],
            ["Maintenance workforce capability", 4, 4, 4, 5, 5, 4, 3, 3, 4, 3, "Capability"],
            ["Battery lifecycle impact", 4, 3, 4, 3, 2, 3, 2, 4, 4, 4, "Lifecycle"],
        ],
        "prototype": {
            "priority": "Fair fleet transition",
            "hypothesis": "A small electric-bus deployment on one route reduces emissions and pollution without reducing reliability or accessibility.",
            "intervention": "Deploy electric buses on one route with safeguards.",
            "owner": "Fleet Transition Programme Lead",
            "participants": ["Operations", "Maintenance", "Drivers", "Accessibility panel"],
            "metric": "Emissions, reliability, operating cost, passenger satisfaction, accessibility, driver feedback and charging performance",
            "success": "Emissions reduction without reliability or accessibility decline",
            "risk": "Reliability or accessibility worsens",
            "expected": "Just fleet-transition experiment",
        },
    },
    {
        "id": "medigen",
        "company": "Medigen Laboratories",
        "sector": "Pharmaceutical and biotechnology",
        "size": "3,200 employees",
        "revenue": "GBP 1bn-2bn",
        "regions": "Regulated laboratory and manufacturing sites",
        "products": "Pharmaceutical and biotechnology products",
        "maturity": "high compliance, fragmented sustainability",
        "data_richness": "high",
        "contradiction_level": "medium",
        "missing_field_level": "medium",
        "regulation": "very high",
        "goal": "Reduce laboratory impact while preserving safety and product quality",
        "barriers": ["Safety requirements", "Regulatory controls", "Lifecycle data gaps", "IP constraints"],
        "business": "Patient safety, product quality, R&D uncertainty, cold-chain reliability and access to medicines shape decisions.",
        "human": "Patients depend on safe products; scientists need flexibility and communities may be affected by waste and water.",
        "planetary": "Laboratories, solvents, hazardous waste, cold-chain logistics, water and medicine disposal create impacts.",
        "journey": [
            ["Research", "Lab experimentation", "Energy, chemicals and ethics", "Scientists, patients", "high", "high"],
            ["Clinical development", "Trials and materials", "Materials and travel", "Clinicians, patients", "medium", "medium"],
            ["Manufacturing", "Production", "Water, solvents and waste", "Manufacturing teams", "high", "high"],
            ["Packaging", "Sterile packaging", "Safety and sterility trade-offs", "Quality, regulators", "medium", "high"],
            ["Distribution", "Cold chain", "Cold-chain energy", "Logistics, patients", "medium", "medium"],
            ["Patient use", "Medicine use", "Access and disposal", "Patients, clinicians", "low", "medium"],
            ["End of life", "Medicine and device disposal", "Ecosystem exposure", "Patients, waste handlers", "low", "low"],
        ],
        "challenges": [
            ["Controlled solvent substitution", 5, 4, 5, 4, 4, 4, 3, 4, 5, 4, "Laboratory"],
            ["Laboratory energy", 4, 4, 4, 2, 5, 5, 4, 3, 3, 2, "Operations"],
            ["Hazardous waste", 4, 4, 5, 3, 4, 4, 3, 3, 4, 3, "Waste"],
            ["Cold-chain impact", 3, 3, 4, 2, 3, 3, 3, 3, 3, 3, "Logistics"],
            ["Medicine disposal", 4, 3, 4, 4, 2, 2, 2, 4, 4, 4, "End of life"],
        ],
        "prototype": {
            "priority": "Controlled solvent substitution",
            "hypothesis": "Substituting one laboratory solvent in a controlled research workflow reduces hazardous impact without reducing research quality or safety.",
            "intervention": "Test one solvent substitution in a controlled research workflow.",
            "owner": "Laboratory Operations Lead",
            "participants": ["Scientists", "Safety", "Quality", "Sustainability"],
            "metric": "Solvent use, hazardous waste, experiment performance, cost, staff acceptance and safety incidents",
            "success": "Hazard reduction without research quality or safety failure",
            "risk": "Safety, quality or regulatory issue",
            "expected": "Controlled laboratory substitution",
        },
    },
]


def score_to_confidence(score: int) -> str:
    return "high" if score >= 4 else "medium" if score == 3 else "low"


def maturity_level(text: str) -> str:
    lowered = text.lower()
    if "advanced" in lowered or "high compliance" in lowered:
        return "mid"
    if "early" in lowered or "low formal" in lowered:
        return "light"
    return "light"


def build_onboarding(fixture: dict) -> dict:
    return {
        "role": "Chief Sustainability Officer",
        "mode": "solo",
        "influence": "Shared decision authority",
        "representing": "Sustainability and transformation",
        "organisationProfileType": "Example or learning organisation",
        "organisationName": fixture["company"],
        "headquarters": fixture["regions"].split(",")[0],
        "regions": fixture["regions"],
        "industry": fixture["sector"],
        "size": fixture["size"],
        "revenueBand": fixture["revenue"],
        "products": fixture["products"],
        "businessModel": "Mixed model",
        "reasons": [fixture["goal"], "Decide what to prioritise"],
        "maturity": fixture["maturity"],
        "barriers": fixture["barriers"],
        "constraints": fixture["barriers"],
        "stakeholders": ["Leadership", "Operations", "Procurement", "Employees", "Customers", "Suppliers"],
        "decisionOwner": fixture["prototype"]["owner"],
        "dataSources": [f"{fixture['data_richness']} internal data", "Stakeholder knowledge", "Operational records"],
        "outputs": ["Organisation context profile", "Priority portfolio", "Prototype experiment card"],
        "confirmAccuracy": "on",
        "confirmVerification": "on",
        "testConditions": {
            "data_richness": fixture["data_richness"],
            "contradiction_level": fixture["contradiction_level"],
            "missing_field_level": fixture["missing_field_level"],
            "sustainability_maturity": fixture["maturity"],
            "regulated_sector": fixture["regulation"] in {"high", "very high"},
            "expected_completion": True,
        },
    }


def empathy_response(fixture: dict, empathy: str, idx: int, area: str, notes: str, signal: str) -> dict:
    confidence = "low" if fixture["data_richness"] == "low" else "medium" if fixture["data_richness"] == "medium" else "high"
    return {
        "id": idx,
        "empathy": empathy,
        "area": area,
        "slug": area.lower().replace(" ", "-"),
        "maturity": maturity_level(fixture["maturity"]),
        "confidence": confidence,
        "scope": "Whole organisation",
        "evidence": f"{fixture['data_richness']} fixture evidence",
        "notes": notes,
        "flags": ["Strategically important", "Review later"] if confidence == "low" else ["Strategically important"],
        "impactSignal": signal,
        "supports": notes,
        "uncertain": "Evidence quality varies by stage and stakeholder group.",
        "important": signal,
        "carryForwardActions": ["problem-signal", "impact-journey"],
    }


def build_explore(fixture: dict) -> dict:
    responses = {}
    rows = [
        ("business", 1, "Strategy and Purpose", fixture["business"], fixture["goal"]),
        ("business", 2, "Finance and Investment", "Commercial pressure and cost constraints affect sustainability choices.", "Financial constraint"),
        ("business", 3, "Operations and Delivery", "Operational routines and incentives shape delivery choices.", "Operational leverage"),
        ("human", 17, "Stakeholder Power", fixture["human"], "Power and participation imbalance"),
        ("human", 18, "Capability and Behaviour", "People need clearer roles, evidence and confidence to participate.", "Capability gap"),
        ("human", 19, "Equity and Wellbeing", "Some groups experience impacts without strong decision power.", "Fairness risk"),
        ("planetary", 30, "Environmental Impact", fixture["planetary"], "Material environmental impact"),
        ("planetary", 31, "Natural Dependencies", "The organisation depends on stable resources, suppliers and operating conditions.", "Dependency risk"),
        ("planetary", 32, "Evidence and Limits", "Some lifecycle impacts remain poorly evidenced.", "Evidence gap"),
    ]
    for empathy, idx, area, notes, signal in rows:
        responses[str(idx)] = empathy_response(fixture, empathy, idx, area, notes, signal)
    return {"responses": responses}


def build_impact(fixture: dict) -> dict:
    stages = []
    layer_items = {}
    relationships = []
    problem_signals = []
    for index, (name, activity, issue, stakeholders, control, evidence) in enumerate(fixture["journey"], start=1):
        stage_id = f"{fixture['id']}-stage-{index}"
        stages.append({"id": stage_id, "name": name, "sequence": index, "description": issue})
        layer_items[stage_id] = {
            "activities": [activity],
            "stakeholders": [part.strip() for part in stakeholders.split(",")],
            "businessEffects": [issue],
            "humanEffects": [f"Stakeholder effect: {stakeholders}"],
            "planetaryEffects": [issue],
            "decisionPoints": [f"Decision at {name}"],
            "control": control,
            "evidenceQuality": evidence,
            "unknowns": [] if evidence == "high" else [f"Evidence gap at {name}"],
        }
        problem_signals.append({
            "id": f"{fixture['id']}-signal-{index}",
            "title": issue,
            "stageId": stage_id,
            "description": f"{issue} during {activity}.",
            "severity": 4 if index <= 3 else 3,
            "confidence": evidence,
            "control": control,
        })
        if index > 1:
            rel_types = ["Dependency", "Delay", "Trade-off", "Bottleneck", "Feedback loop", "Risk transfer", "Reinforcing loop"]
            rel_type = rel_types[(index - 2) % len(rel_types)]
            relationships.append({
                "id": f"{fixture['id']}-rel-{index}",
                "source": stages[index - 2]["id"],
                "target": stage_id,
                "type": rel_type,
                "confidence": "High" if evidence == "high" else "Medium" if evidence == "medium" else "Low",
                "description": f"{stages[index - 2]['name']} creates a {rel_type.lower()} affecting {name}, especially around {issue.lower()}.",
            })
    if len(stages) >= 5:
        relationships.append({
            "id": f"{fixture['id']}-rel-feedback-final",
            "source": stages[-2]["id"],
            "target": stages[1]["id"],
            "type": "Feedback loop",
            "confidence": "Medium",
            "description": f"Learning from {stages[-2]['name']} should feed back into {stages[1]['name']} decisions before scaling.",
        })
    return {
        "scope": {
            "journeyType": "product-value-chain",
            "primaryFocus": "Whole organisation",
            "timeframe": "Current state",
            "startPoint": fixture["journey"][0][0],
            "endPoint": fixture["journey"][-1][0],
            "insideBoundary": "Main value-chain stages in the MVP fixture.",
            "outsideBoundary": "Wider market, regulation and supplier conditions.",
        },
        "stages": stages,
        "layerItems": layer_items,
        "relationships": relationships,
        "problemSignals": problem_signals,
        "opportunities": [{"id": f"{fixture['id']}-opp-1", "title": fixture["prototype"]["expected"], "description": fixture["prototype"]["intervention"]}],
        "activeLayer": "planetary",
        "activeStage": stages[0]["id"],
    }


def build_priority(fixture: dict, impact_state_id: str) -> dict:
    problems = []
    for index, (title, severity, urgency, strategic, stakeholder, influence, evidence, feasibility, effort, leverage, unintended, cluster) in enumerate(fixture["challenges"], start=1):
        problem_id = f"{fixture['id']}-problem-{index}"
        confidence = evidence
        problems.append({
            "id": problem_id,
            "title": title,
            "description": f"{title} matters for {fixture['company']} because {fixture['goal'].lower()}.",
            "source": "dummy-fixture",
            "cluster": cluster,
            "status": "selected" if index <= 3 else "confirmed",
            "confidence": confidence,
            "spectrum": "light" if evidence <= 2 else "mid",
            "cynefin": "complex" if unintended >= 3 or evidence <= 2 else "complicated",
            "scores": {
                "impact": severity,
                "urgency": urgency,
                "strategic": strategic,
                "stakeholder": stakeholder,
                "influence": influence,
                "confidence": confidence,
                "evidence": evidence,
                "readiness": feasibility,
                "effort": effort,
                "leverage": leverage,
                "unintended": unintended,
            },
            "evidence": score_to_confidence(evidence),
        })
    return {
        "problems": problems,
        "weights": deepcopy(server.DEFAULT_PRIORITY_WEIGHTS),
        "selectedIds": [problem["id"] for problem in problems[:3]],
        "reviewed": True,
        "sourceImpactJourneyStateId": impact_state_id,
    }


def build_intervention(fixture: dict, priority_state_id: str, portfolio_id: str, priority_form: dict) -> dict:
    primary = priority_form["problems"][0]
    selected_option_id = f"{fixture['id']}-option-1"
    pathway_id = f"{fixture['id']}-pathway-1"
    review_date = (date.today() + timedelta(days=56)).isoformat()
    prototype = fixture["prototype"]
    prototype_type = recommended_prototype_type(fixture, primary)
    pathway = {
        "id": pathway_id,
        "problemId": primary["id"],
        "rank": 1,
        "title": prototype["priority"],
        "problemDefinition": primary["description"],
        "evidenceSummary": f"{fixture['data_richness']} data, {fixture['missing_field_level']} missing fields.",
        "unknowns": ["Evidence limitations remain"] if fixture["missing_field_level"] in {"medium", "high"} else [],
        "spectrum": primary["spectrum"],
        "cynefin": primary["cynefin"],
        "readiness": primary["scores"]["readiness"],
        "influence": primary["scores"]["influence"],
        "leverage": primary["scores"]["leverage"],
        "desiredOutcome": prototype["expected"],
        "beneficiaries": prototype["participants"],
        "changes": ["process", "decision", "evidence"],
        "nonNegotiables": "Safety, fairness and evidence quality",
        "timeframe": "0-3 months",
        "backcastSteps": ["Confirm owner", "Run prototype", "Review evidence"],
        "decisionAnswers": {"clarity": "mixed", "alignment": "yes", "testable": "yes"},
        "decisionOutcome": "experiment",
        "decisionRationale": "A bounded prototype reduces uncertainty before wider implementation.",
        "interventionOptions": [
            {
                "id": selected_option_id,
                "family": "process",
                "status": "selected",
                "title": prototype["intervention"],
                "description": prototype["hypothesis"],
                "mechanism": "Test the riskiest assumption in a contained setting.",
                "impact": 4,
                "effort": 3,
                "risk": 3,
            }
        ],
        "selectedInterventionId": selected_option_id,
        "horizons": [
            {"type": "h1", "title": "Horizon 1", "timeframe": "0-3 months", "objective": "Run prototype", "actions": ["Confirm scope", "Collect evidence"], "owner": prototype["owner"], "decisionDate": review_date},
            {"type": "h2", "title": "Horizon 2", "timeframe": "3-12 months", "objective": "Iterate or expand", "actions": ["Review result", "Adjust design"], "owner": prototype["owner"], "decisionDate": ""},
            {"type": "h3", "title": "Horizon 3", "timeframe": "12+ months", "objective": "Scale if evidence supports", "actions": ["Build capability", "Set governance"], "owner": prototype["owner"], "decisionDate": ""},
        ],
        "prototypeType": prototype_type,
        "experiment": {
            "title": prototype["priority"],
            "hypothesis": prototype["hypothesis"],
            "learningObjective": prototype["expected"],
            "method": prototype["intervention"],
            "decisionThreshold": prototype["success"],
            "startDate": date.today().isoformat(),
            "endDate": review_date,
            "status": "draft",
        },
        "owners": {
            "executiveSponsor": "Executive sponsor",
            "pathwayOwner": prototype["owner"],
            "experimentOwner": prototype["owner"],
            "decisionMaker": "Leadership team",
            "dataOwner": "Sustainability analyst",
            "riskOwner": "Risk owner",
            "cadence": "monthly",
        },
        "metrics": [
            {
                "name": prototype["metric"],
                "category": "learning",
                "unit": "mixed evidence set",
                "baseline": "Current baseline to be confirmed before launch",
                "target": prototype["success"],
                "owner": prototype["owner"],
                "frequency": "baseline, midpoint and final review",
                "dataSource": "Operational data, stakeholder feedback and prototype evidence log",
            },
            {
                "name": "Human outcome protected",
                "category": "outcome",
                "unit": "guardrail status",
                "baseline": "No explicit guardrail tested",
                "target": "No material harm to affected stakeholders",
                "owner": prototype["owner"],
                "frequency": "weekly during prototype",
                "dataSource": "Participant feedback and issue log",
            },
        ],
        "risks": [
            {
                "category": "sector-specific",
                "description": prototype["risk"],
                "likelihood": 2 if fixture["data_richness"] == "high" else 3,
                "severity": 4 if fixture["regulation"] in {"high", "very high"} else 3,
                "mitigation": f"Assign {prototype['owner']} as accountable owner, set a pre-launch baseline, and stop if the guardrail is breached.",
                "owner": prototype["owner"],
                "watchSignal": "Unexpected harm, weak evidence, delay or stakeholder objection",
                "stopCondition": "Stop or redesign if safety, fairness, quality, access or evidence thresholds are breached",
            }
        ],
        "reviewDate": review_date,
        "completed": True,
    }
    return {
        "sourcePriorityStateId": priority_state_id,
        "sourcePriorityPortfolioId": portfolio_id,
        "pathways": [pathway],
        "activeId": pathway_id,
        "primaryIds": [pathway_id],
        "reviewed": True,
    }


def run_fixture(fixture: dict) -> dict:
    session_id = f"dummy-{fixture['id']}"
    onboarding_form = build_onboarding(fixture)
    onboarding = server.complete_onboarding({"anonymousSessionId": session_id, "formData": onboarding_form})
    journey_id = onboarding.get("journeyId") or onboarding.get("contextProfile", {}).get("journeyId") or ""

    explore_form = build_explore(fixture)
    business = server.save_explore_business({"anonymousSessionId": session_id, "journeyId": journey_id, "formData": explore_form}, status="business_complete")
    human = server.save_explore_human({"anonymousSessionId": session_id, "journeyId": journey_id, "formData": explore_form}, status="human_complete")
    planetary = server.save_explore_planetary({"anonymousSessionId": session_id, "journeyId": journey_id, "formData": explore_form}, status="planetary_complete")

    impact_form = build_impact(fixture)
    impact = server.save_impact_journey({"anonymousSessionId": session_id, "journeyId": journey_id, "formData": impact_form}, status="completed")
    impact_state_id = impact.get("stateId", "")

    priority_form = build_priority(fixture, impact_state_id)
    priority = server.save_priority_state({"anonymousSessionId": session_id, "journeyId": journey_id, "formData": priority_form}, status="completed")
    priority_state_id = priority.get("stateId", "")
    priority_portfolio_id = priority.get("handover", {}).get("source", {}).get("portfolioId", "")

    intervention_form = build_intervention(fixture, priority_state_id, priority_portfolio_id, priority.get("formData", priority_form))
    intervention = server.save_intervention_state({"anonymousSessionId": session_id, "journeyId": journey_id, "formData": intervention_form}, status="completed")

    priority_analysis = priority.get("analysis", {})
    ranked_ids = priority_analysis.get("rankedProblemIds", [])
    ranked_titles = []
    problem_by_id = {problem["id"]: problem for problem in priority.get("formData", {}).get("problems", [])}
    for problem_id in ranked_ids[:3]:
        if problem_id in problem_by_id:
            ranked_titles.append(problem_by_id[problem_id]["title"])

    recommendations = priority_analysis.get("recommendations", [])
    categories = [item.get("category") for item in recommendations[:5]]
    intervention_analysis = intervention.get("analysis", {})

    failures = []
    for label, result in [
        ("onboarding", onboarding),
        ("business", business),
        ("human", human),
        ("planetary", planetary),
        ("impact", impact),
        ("priority", priority),
        ("prototype", intervention),
    ]:
        if not result.get("ok", True):
            failures.append(f"{label}: {result.get('error') or result.get('validation')}")

    expected_match = expected_direction_match(fixture, ranked_titles, recommendations, intervention_analysis)
    recommendation_diversity = len(set([str(item) for item in categories if item]))
    return {
        "company_id": fixture["id"],
        "company": fixture["company"],
        "sector": fixture["sector"],
        "size": fixture["size"],
        "maturity": fixture["maturity"],
        "data_richness": fixture["data_richness"],
        "contradiction_level": fixture["contradiction_level"],
        "missing_field_level": fixture["missing_field_level"],
        "regulation": fixture["regulation"],
        "expected_direction": fixture["prototype"]["expected"],
        "journey_id": journey_id,
        "onboarding_ok": bool(onboarding.get("ok", True)),
        "impact_ok": bool(impact.get("ok", False)),
        "priority_ok": bool(priority.get("ok", False)),
        "prototype_ok": bool(intervention.get("ok", False)),
        "impact_completion": impact.get("analysis", {}).get("completionPercentage", 0),
        "priority_completion": priority_analysis.get("completionPercentage", 0),
        "prototype_completion": intervention_analysis.get("completionPercentage", 0),
        "top_ranked_priorities": " | ".join(ranked_titles),
        "recommendation_categories": " | ".join([str(item) for item in categories if item]),
        "recommendation_diversity": recommendation_diversity,
        "portfolio_warnings": " | ".join(priority_analysis.get("portfolioWarnings", [])),
        "prototype_warnings": " | ".join(intervention_analysis.get("portfolioWarnings", [])),
        "experiment_ready_count": intervention_analysis.get("experimentReadyCount", 0),
        "prototype_hypothesis": fixture["prototype"]["hypothesis"],
        "prototype_metric": fixture["prototype"]["metric"],
        "validation_failures": " | ".join(failures),
        "straightforward": "yes" if not failures and priority_analysis.get("completionPercentage", 0) >= 80 else "review",
        "expected_direction_match": expected_match,
        "differentiation_signal": "passes" if expected_match and recommendation_diversity >= 2 else "review",
        "raw": {
            "onboarding": onboarding,
            "business": business,
            "human": human,
            "planetary": planetary,
            "impact": impact,
            "priority": priority,
            "prototype": intervention,
        },
    }


def recommended_prototype_type(fixture: dict, primary_problem: dict) -> str:
    text = " ".join(
        [
            fixture["sector"],
            fixture["human"],
            fixture["prototype"]["priority"],
            fixture["prototype"]["hypothesis"],
            primary_problem.get("cluster", ""),
        ]
    ).lower()
    if any(term in text for term in ["worker", "customer", "fairness", "accessibility", "community", "passenger", "clinician", "farmer", "behaviour"]):
        return "behaviour"
    if any(term in text for term in ["supplier", "traceability", "procurement"]):
        return "supply-chain"
    if any(term in text for term in ["cloud", "digital", "data", "ai"]):
        return "digital"
    if any(term in text for term in ["material", "solvent", "product"]):
        return "product"
    return "process"


def expected_direction_match(fixture: dict, ranked_titles: list[str], recommendations: list[dict], intervention_analysis: dict) -> bool:
    expected = fixture["prototype"]["expected"].lower()
    haystack = " ".join(
        ranked_titles
        + [fixture["prototype"]["priority"], fixture["prototype"]["hypothesis"], fixture["prototype"]["intervention"]]
        + [str(item.get("category", "")) + " " + str(item.get("action", "")) for item in recommendations]
        + [json.dumps(intervention_analysis.get("outputs", {}), ensure_ascii=False)]
    ).lower()
    keyword_groups = {
        "supplier and material evidence": ["supplier", "material", "metal"],
        "traceability, labour and claims": ["traceability", "labour", "claims"],
        "finance and lending decisions": ["finance", "lending", "loan", "credit"],
        "clinically safe emissions intervention": ["clinical", "anaesthetic", "safety"],
        "farm, water and nature resilience": ["farm", "water", "soil", "nature"],
        "early-stage design leverage": ["design", "concept", "planning"],
        "digital and cloud impact evidence": ["cloud", "digital", "compute", "ai"],
        "validate circular impact": ["circular", "subscription", "churn", "transport"],
        "just fleet-transition experiment": ["fleet", "bus", "accessibility", "route"],
        "controlled laboratory substitution": ["laboratory", "solvent", "controlled"],
    }
    keywords = keyword_groups.get(expected, expected.replace(",", "").split())
    return any(keyword in haystack for keyword in keywords)


def cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: cell(row.get(key, "")) for key in fieldnames})


def company_lookup() -> dict[str, dict]:
    return {fixture["id"]: fixture for fixture in FIXTURES}


def write_detailed_outputs(results: list[dict]) -> None:
    DETAILED_DIR.mkdir(exist_ok=True)
    fixtures = company_lookup()

    summary_rows = [{key: value for key, value in result.items() if key != "raw"} for result in results]

    onboarding_rows = []
    explore_rows = []
    explore_output_rows = []
    impact_scope_rows = []
    impact_stage_rows = []
    impact_relationship_rows = []
    impact_signal_rows = []
    impact_analysis_rows = []
    priority_problem_rows = []
    priority_recommendation_rows = []
    priority_trace_rows = []
    empathy_integration_rows = []
    priority_cluster_rows = []
    prototype_pathway_rows = []
    prototype_experiment_rows = []
    prototype_metric_rows = []
    prototype_risk_rows = []
    generated_asset_rows = []
    validation_rows = []

    for result in results:
        fixture = fixtures[result["company_id"]]
        raw = result["raw"]
        onboarding_form = raw.get("onboarding", {}).get("formData") or build_onboarding(fixture)
        onboarding_context = raw.get("onboarding", {}).get("contextProfile", {})
        onboarding_route = raw.get("onboarding", {}).get("recommendedRoute", {})
        onboarding_rows.append({
            "company_id": result["company_id"],
            "company": result["company"],
            "journey_id": result["journey_id"],
            "sector": result["sector"],
            "size": result["size"],
            "revenue": fixture["revenue"],
            "regions": fixture["regions"],
            "products": fixture["products"],
            "maturity": result["maturity"],
            "data_richness": result["data_richness"],
            "contradiction_level": result["contradiction_level"],
            "missing_field_level": result["missing_field_level"],
            "regulation": result["regulation"],
            "goal": fixture["goal"],
            "barriers": fixture["barriers"],
            "stakeholders": onboarding_form.get("stakeholders", []),
            "data_sources": onboarding_form.get("dataSources", []),
            "outputs_requested": onboarding_form.get("outputs", []),
            "context_profile": onboarding_context,
            "recommended_route": onboarding_route,
        })

        explore_form = build_explore(fixture)
        for response in explore_form["responses"].values():
            explore_rows.append({
                "company_id": result["company_id"],
                "company": result["company"],
                "empathy": response.get("empathy"),
                "question_id": response.get("id"),
                "area": response.get("area"),
                "maturity": response.get("maturity"),
                "confidence": response.get("confidence"),
                "scope": response.get("scope"),
                "evidence": response.get("evidence"),
                "notes": response.get("notes"),
                "impact_signal": response.get("impactSignal"),
                "flags": response.get("flags", []),
                "supports": response.get("supports"),
                "uncertain": response.get("uncertain"),
                "important": response.get("important"),
                "carry_forward_actions": response.get("carryForwardActions", []),
            })
        for empathy in ["business", "human", "planetary"]:
            outputs = raw.get(empathy, {}).get("outputs", {})
            for key, value in outputs.items():
                explore_output_rows.append({
                    "company_id": result["company_id"],
                    "company": result["company"],
                    "empathy": empathy,
                    "output_key": key,
                    "output_value": value,
                })

        impact_form = build_impact(fixture)
        impact_analysis = raw.get("impact", {}).get("analysis", {})
        impact_scope_rows.append({
            "company_id": result["company_id"],
            "company": result["company"],
            "impact_state_id": raw.get("impact", {}).get("stateId", ""),
            **impact_form["scope"],
            "analysis": impact_analysis,
            "completion": result["impact_completion"],
        })
        for stage in impact_form["stages"]:
            layer = impact_form["layerItems"].get(stage["id"], {})
            impact_stage_rows.append({
                "company_id": result["company_id"],
                "company": result["company"],
                "stage_id": stage["id"],
                "sequence": stage.get("sequence"),
                "stage_name": stage.get("name"),
                "description": stage.get("description"),
                "activities": layer.get("activities", []),
                "stakeholders": layer.get("stakeholders", []),
                "business_effects": layer.get("businessEffects", []),
                "human_effects": layer.get("humanEffects", []),
                "planetary_effects": layer.get("planetaryEffects", []),
                "decision_points": layer.get("decisionPoints", []),
                "control": layer.get("control"),
                "evidence_quality": layer.get("evidenceQuality"),
                "unknowns": layer.get("unknowns", []),
            })
        for relationship in impact_form["relationships"]:
            impact_relationship_rows.append({"company_id": result["company_id"], "company": result["company"], **relationship})
        for signal in impact_form["problemSignals"]:
            impact_signal_rows.append({"company_id": result["company_id"], "company": result["company"], **signal})
        for key, value in impact_analysis.items():
            impact_analysis_rows.append({
                "company_id": result["company_id"],
                "company": result["company"],
                "analysis_key": key,
                "analysis_value": value,
            })

        priority_form = raw.get("priority", {}).get("formData", {})
        priority_analysis = raw.get("priority", {}).get("analysis", {})
        selected_ids = set(priority_form.get("selectedIds", []))
        ranked = priority_analysis.get("rankedProblemIds", [])
        for problem in priority_form.get("problems", []):
            scores = problem.get("scores", {})
            priority_problem_rows.append({
                "company_id": result["company_id"],
                "company": result["company"],
                "problem_id": problem.get("id"),
                "title": problem.get("title"),
                "description": problem.get("description"),
                "cluster": problem.get("cluster"),
                "status": problem.get("status"),
                "selected": problem.get("id") in selected_ids,
                "rank": ranked.index(problem.get("id")) + 1 if problem.get("id") in ranked else "",
                "spectrum": problem.get("spectrum"),
                "cynefin": problem.get("cynefin"),
                "overall": problem.get("overall"),
                "impact": scores.get("impact"),
                "urgency": scores.get("urgency"),
                "strategic": scores.get("strategic"),
                "stakeholder": scores.get("stakeholder"),
                "influence": scores.get("influence"),
                "confidence": scores.get("confidence"),
                "evidence": scores.get("evidence"),
                "readiness": scores.get("readiness"),
                "effort": scores.get("effort"),
                "leverage": scores.get("leverage"),
                "unintended": scores.get("unintended"),
                "score_trace": problem.get("scoreTrace", {}),
                "evidence_trace": problem.get("evidenceTrace", {}),
            })
            trace = problem.get("scoreTrace", {})
            for contribution in trace.get("contributions", []) if isinstance(trace, dict) else []:
                priority_trace_rows.append({
                    "company_id": result["company_id"],
                    "company": result["company"],
                    "problem_id": problem.get("id"),
                    "problem_title": problem.get("title"),
                    **contribution,
                })
        for recommendation in priority_analysis.get("recommendations", []):
            problem = next((item for item in priority_form.get("problems", []) if item.get("id") == recommendation.get("problemId")), {})
            priority_recommendation_rows.append({
                "company_id": result["company_id"],
                "company": result["company"],
                "problem_id": recommendation.get("problemId"),
                "problem_title": problem.get("title"),
                "category": recommendation.get("category"),
                "action": recommendation.get("action"),
                "rationale": recommendation.get("rationale"),
                "confidence": recommendation.get("confidence"),
                "why_this": recommendation.get("whyThis"),
                "uncertainty": recommendation.get("uncertainty"),
                "source_evidence": recommendation.get("sourceEvidence"),
                "score_trace": recommendation.get("scoreTrace"),
            })
        for row in priority_analysis.get("threeEmpathiesIntegration", []):
            empathy_integration_rows.append({"company_id": result["company_id"], "company": result["company"], **row})
        for cluster in priority_analysis.get("clusters", []):
            priority_cluster_rows.append({"company_id": result["company_id"], "company": result["company"], **cluster})

        intervention_form = raw.get("prototype", {}).get("formData", {})
        intervention_analysis = raw.get("prototype", {}).get("analysis", {})
        for pathway in intervention_form.get("pathways", []):
            selected_option = next((item for item in pathway.get("interventionOptions", []) if item.get("id") == pathway.get("selectedInterventionId")), {})
            owners = pathway.get("owners", {})
            experiment = pathway.get("experiment", {})
            prototype_pathway_rows.append({
                "company_id": result["company_id"],
                "company": result["company"],
                "pathway_id": pathway.get("id"),
                "title": pathway.get("title"),
                "problem_definition": pathway.get("problemDefinition"),
                "desired_outcome": pathway.get("desiredOutcome"),
                "decision_outcome": pathway.get("decisionOutcome"),
                "decision_rationale": pathway.get("decisionRationale"),
                "selected_intervention": selected_option.get("title"),
                "prototype_type": pathway.get("prototypeType"),
                "unknowns": pathway.get("unknowns", []),
                "owner": owners.get("pathwayOwner"),
                "experiment_owner": owners.get("experimentOwner"),
                "review_date": pathway.get("reviewDate"),
                "completed": pathway.get("completed"),
                "horizons": pathway.get("horizons", []),
            })
            prototype_experiment_rows.append({
                "company_id": result["company_id"],
                "company": result["company"],
                "pathway_id": pathway.get("id"),
                "experiment_title": experiment.get("title"),
                "hypothesis": experiment.get("hypothesis"),
                "learning_objective": experiment.get("learningObjective"),
                "method": experiment.get("method"),
                "decision_threshold": experiment.get("decisionThreshold"),
                "start_date": experiment.get("startDate"),
                "end_date": experiment.get("endDate"),
                "status": experiment.get("status"),
                "participants": pathway.get("beneficiaries", []),
                "risk": fixture["prototype"]["risk"],
                "expected_direction": fixture["prototype"]["expected"],
            })
            for metric in pathway.get("metrics", []):
                prototype_metric_rows.append({"company_id": result["company_id"], "company": result["company"], "pathway_id": pathway.get("id"), **metric})
            for risk in pathway.get("risks", []):
                prototype_risk_rows.append({"company_id": result["company_id"], "company": result["company"], "pathway_id": pathway.get("id"), **risk})

        outputs = intervention_analysis.get("outputs", {})
        for asset_name, asset_value in outputs.items():
            generated_asset_rows.append({
                "company_id": result["company_id"],
                "company": result["company"],
                "asset_stage": "prototype",
                "asset_name": asset_name,
                "asset_value": asset_value,
            })
        for key, value in priority_analysis.items():
            if key in {"recommendations", "clusters", "duplicatePairs", "selectedProblems", "rankedProblemIds"}:
                generated_asset_rows.append({
                    "company_id": result["company_id"],
                    "company": result["company"],
                    "asset_stage": "prioritisation",
                    "asset_name": key,
                    "asset_value": value,
                })
        for key, value in impact_analysis.items():
            generated_asset_rows.append({
                "company_id": result["company_id"],
                "company": result["company"],
                "asset_stage": "impact_journey",
                "asset_name": key,
                "asset_value": value,
            })

        validation_rows.extend([
            {
                "company_id": result["company_id"],
                "company": result["company"],
                "stage": "impact",
                "ok": result["impact_ok"],
                "completion": result["impact_completion"],
                "warnings": raw.get("impact", {}).get("validation", {}).get("warnings", []),
                "errors": raw.get("impact", {}).get("validation", {}).get("errors", []),
            },
            {
                "company_id": result["company_id"],
                "company": result["company"],
                "stage": "prioritisation",
                "ok": result["priority_ok"],
                "completion": result["priority_completion"],
                "warnings": raw.get("priority", {}).get("validation", {}).get("warnings", []),
                "errors": raw.get("priority", {}).get("validation", {}).get("blockingIssues", []),
            },
            {
                "company_id": result["company_id"],
                "company": result["company"],
                "stage": "prototype",
                "ok": result["prototype_ok"],
                "completion": result["prototype_completion"],
                "warnings": raw.get("prototype", {}).get("validation", {}).get("warnings", []) + intervention_analysis.get("portfolioWarnings", []),
                "errors": raw.get("prototype", {}).get("validation", {}).get("blockingIssues", []),
            },
        ])

    write_csv(DETAILED_DIR / "00_summary.csv", summary_rows, list(summary_rows[0].keys()))
    write_csv(DETAILED_DIR / "01_onboarding_context.csv", onboarding_rows, list(onboarding_rows[0].keys()))
    write_csv(DETAILED_DIR / "02_explore_responses.csv", explore_rows, list(explore_rows[0].keys()))
    write_csv(DETAILED_DIR / "03_explore_outputs.csv", explore_output_rows, list(explore_output_rows[0].keys()) if explore_output_rows else ["company_id", "company", "empathy", "output_key", "output_value"])
    write_csv(DETAILED_DIR / "04_impact_scope.csv", impact_scope_rows, list(impact_scope_rows[0].keys()))
    write_csv(DETAILED_DIR / "05_impact_stages.csv", impact_stage_rows, list(impact_stage_rows[0].keys()))
    write_csv(DETAILED_DIR / "06_impact_relationships.csv", impact_relationship_rows, list(impact_relationship_rows[0].keys()))
    write_csv(DETAILED_DIR / "07_impact_problem_signals.csv", impact_signal_rows, list(impact_signal_rows[0].keys()))
    write_csv(DETAILED_DIR / "08_impact_analysis_outputs.csv", impact_analysis_rows, list(impact_analysis_rows[0].keys()))
    write_csv(DETAILED_DIR / "09_priority_problem_scores.csv", priority_problem_rows, list(priority_problem_rows[0].keys()))
    write_csv(DETAILED_DIR / "10_priority_recommendations.csv", priority_recommendation_rows, list(priority_recommendation_rows[0].keys()))
    write_csv(DETAILED_DIR / "11_priority_clusters.csv", priority_cluster_rows, list(priority_cluster_rows[0].keys()))
    write_csv(DETAILED_DIR / "12_prototype_pathways.csv", prototype_pathway_rows, list(prototype_pathway_rows[0].keys()))
    write_csv(DETAILED_DIR / "13_prototype_experiments.csv", prototype_experiment_rows, list(prototype_experiment_rows[0].keys()))
    write_csv(DETAILED_DIR / "14_prototype_metrics.csv", prototype_metric_rows, list(prototype_metric_rows[0].keys()))
    write_csv(DETAILED_DIR / "15_prototype_risks.csv", prototype_risk_rows, list(prototype_risk_rows[0].keys()))
    write_csv(DETAILED_DIR / "16_generated_assets_outputs.csv", generated_asset_rows, list(generated_asset_rows[0].keys()))
    write_csv(DETAILED_DIR / "17_validation_warnings_failures.csv", validation_rows, list(validation_rows[0].keys()))
    write_csv(DETAILED_DIR / "18_priority_score_trace.csv", priority_trace_rows, list(priority_trace_rows[0].keys()) if priority_trace_rows else ["company_id", "company", "problem_id", "problem_title", "factor", "score", "weight", "contribution", "direction", "explanation"])
    write_csv(DETAILED_DIR / "19_three_empathies_integration.csv", empathy_integration_rows, list(empathy_integration_rows[0].keys()) if empathy_integration_rows else ["company_id", "company", "problemId", "title", "businessEvidence", "humanEvidence", "planetaryEvidence", "missingPerspectives", "status"])


def write_outputs(results: list[dict]) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    flat_rows = [{key: value for key, value in result.items() if key != "raw"} for result in results]
    fieldnames = list(flat_rows[0].keys())
    with RESULTS_CSV.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_rows)
    write_detailed_outputs(results)
    RESULTS_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    GOOGLE_SHEETS_NOTE.write_text(
        "\n".join(
            [
                "# Google Sheets import",
                "",
                "The test runner writes a summary CSV here:",
                "",
                f"- `{RESULTS_CSV}`",
                "",
                "It also writes detailed Google Sheets tabs as separate CSV files here:",
                "",
                f"- `{DETAILED_DIR}/`",
                "",
                "Recommended import order:",
                "",
                "1. Import `00_summary.csv` as the first sheet.",
                "2. Import each numbered CSV from `01_...` to `19_...` as additional sheets.",
                "3. Keep the file number prefixes as sheet/tab names so cross-stage comparison remains easy.",
                "",
                "A direct Google Sheets API push can be added later, but it requires Google Cloud credentials and OAuth/service-account setup.",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    server.seed_database()
    results = [run_fixture(fixture) for fixture in FIXTURES]
    write_outputs(results)
    failures = [result for result in results if result["validation_failures"]]
    print(f"Ran {len(results)} Green Spectrum dummy-company tests.")
    print(f"CSV: {RESULTS_CSV}")
    print(f"JSON: {RESULTS_JSON}")
    print(f"Google Sheets note: {GOOGLE_SHEETS_NOTE}")
    print(f"Runs needing review: {len(failures)}")
    for result in results:
        print(f"- {result['company']}: priority={result['priority_completion']}%, prototype={result['prototype_completion']}%, direction={result['expected_direction']}")


if __name__ == "__main__":
    main()
