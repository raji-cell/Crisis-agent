# Product Requirements Document (PRD): Smart Campus Resource Allocation AI Agent

## 1\. Executive Summary

The Smart Campus Resource Allocation system is an autonomous, AI-driven platform designed to manage and optimize the utilization of university assets, including classrooms, laboratories, specialized equipment, and faculty time. By leveraging a multi-agent architecture powered by Lyzr, Qdrant, and Enkrypt AI, the system transitions campus management from a manual, reactive process to a proactive, intelligent workflow that maximizes resource efficiency and minimizes scheduling conflicts.

## 2\. Problem Statement

College departments currently struggle with manual resource allocation, leading to:

* **Scheduling Clashes:** Overlapping bookings for the same room or equipment.
* **Underutilization:** Resources remaining vacant due to rigid scheduling or lack of real-time visibility.
* **Manual Overhead:** Administrative staff spending excessive time negotiating between departments.
* **Last-Minute Disruptions:** Inability to adapt quickly to equipment breakdowns or sudden changes in faculty availability.

## 3\. Goals \& Objectives

* **Automate Scheduling:** Reduce manual intervention in routine booking by 80%.
* **Optimize Utilization:** Increase the effective usage rate of high-value labs and equipment.
* **Conflict Resolution:** Provide autonomous negotiation and compromise suggestions when resource contention occurs.
* **Policy Enforcement:** Ensure all allocations adhere to institutional priorities (e.g., graduating seniors, exam weeks).
* **Real-time Adaptation:** Use IoT data to reallocate "ghost-booked" rooms (booked but empty).

## 4\. Target Users / Stakeholders

* **Administrative Staff:** To oversee campus-wide operations and handle high-level overrides.
* **Faculty \& Researchers:** To request labs, equipment, and lecture halls for academic purposes.
* **Student Organizations:** To book event spaces and meeting rooms.
* **Facility Managers:** To monitor resource health and occupancy.

## 5\. Functional Requirements

### 5.1. Resource Request \& Portal

* Users must be able to submit resource requests (time, duration, resource type, priority) via a web interface.
* The system must display a real-time calendar view of resource availability.

### 5.2. Autonomous Orchestration (Lyzr)

* **Lyzr Campus Orchestrator:** Must act as the central "brain," decomposing requests into sub-tasks for specialized agents.
* **Scheduling Optimization Agent:** Must perform mathematical fitting of requests into available slots using optimization logic (OptaPlanner).
* **Conflict Resolution Agent:** Must autonomously analyze competing requests and suggest alternatives or compromises based on historical priority data.

### 5.3. Semantic Memory \& Context (Qdrant)

* The system must store and retrieve "semantic memory" regarding departmental preferences, historical usage patterns, and unstated constraints.
* The agent must use vector search to find "similar past resolutions" to apply to current conflicts.

### 5.4. Safety \& Policy Guardrails (Enkrypt AI)

* All AI-generated responses and decisions must be scrubbed for PII (Personally Identifiable Information).
* The system must prevent "hallucinations" regarding room availability or non-existent equipment.
* Enforce institutional hierarchy (e.g., Departmental exams take priority over club meetings).

### 5.5. Real-time Monitoring (IoT)

* The system must ingest data from occupancy sensors to detect if a booked resource is actually in use.
* The agent must have the authority to release a resource if it remains unoccupied for a defined threshold.

## 6\. Non-Functional Requirements

* **Scalability:** Must support concurrent requests from multiple departments across a large campus.
* **Reliability:** The system must maintain a 99.9% uptime, as it serves as the primary scheduling tool.
* **Latency:** Resource recommendations and conflict resolutions should be generated within seconds.
* **Security:** Ensure faculty and student data is protected and access is restricted based on roles.

## 7\. System Architecture Overview

The system follows a modular, agentic architecture:

1. **Client Layer:** React-based portal for user interaction.
2. **Gateway Layer:** Kong/AWS API Gateway for routing and security.
3. **Agent Core:** Lyzr Orchestrator managing specialized workers (Scheduling \& Conflict Resolution).
4. **Safety Layer:** Enkrypt AI Sentry sitting between the Orchestrator and the LLM.
5. **Data Layer:** PostgreSQL for structured inventory and Qdrant for semantic memory.
6. **Integration Layer:** IoT gateways for occupancy and External APIs for calendar syncing.

## 8\. Tech Stack

* **Frontend:** React, Tailwind CSS, FullCalendar.
* **Agent Orchestration:** Lyzr SDK, LangGraph, Python.
* **Vector Database:** Qdrant.
* **Relational Database:** PostgreSQL, SQLAlchemy.
* **Guardrails:** Enkrypt AI Sentry.
* **LLM Providers:** OpenAI GPT-4o, Anthropic Claude 3.5.
* **API Management:** Kong / AWS API Gateway.
* **IoT Protocol:** MQTT.
* **Optimization Engine:** OptaPlanner.

## 9\. Data Requirements

* **Relational Data (PostgreSQL):**

  * Resource Inventory (Room IDs, Equipment Specs).
  * User Profiles (Roles, Departmental Affiliation).
  * Transaction Logs (Booking history).
* **Vector Data (Qdrant):**

  * Departmental preference embeddings.
  * Historical conflict resolution strategies.
  * Policy document embeddings.

## 10\. API Specifications

* **POST /request/allocate:** Submit a new resource request.
* **GET /resource/status:** Real-time availability including IoT occupancy data.
* **POST /agent/resolve:** Trigger manual intervention or view AI-suggested conflict resolutions.
* **External Sync:** Bi-directional sync with Google Calendar and Microsoft Graph APIs.

## 11\. Security Requirements

* **Authentication:** OAuth2/OpenID Connect for campus-wide SSO.
* **Authorization:** Role-Based Access Control (RBAC) to restrict high-value lab bookings.
* **Data Protection:** Enkrypt AI to mask sensitive faculty data before processing by external LLMs.
* **Audit Logs:** Every autonomous action taken by the Lyzr Orchestrator must be logged for accountability.

## 12\. Deployment \& Infrastructure

* **Cloud:** AWS (suggested) or Hybrid Cloud.
* **Containerization:** All microservices (Lyzr workers, API Gateway) to be containerized using Docker.
* **Orchestration:** Kubernetes for managing agent scaling.
* **CI/CD:** Automated testing for agent logic to ensure scheduling rules are not broken during updates.

## 13\. Success Metrics

* **Utilization Rate:** % increase in hours resources are utilized.
* **Conflict Rate:** Number of double-bookings or manual overrides required per month.
* **User Satisfaction:** Survey scores from faculty and students regarding ease of booking.
* **Response Time:** Average time from request submission to confirmed allocation.

## 14\. Timeline \& Milestones

* **Phase 1 (Weeks 1-2):** Core Agent Development (Lyzr Orchestrator + Qdrant Memory setup).
* **Phase 2 (Weeks 3-4):** Integration with PostgreSQL Inventory and Enkrypt AI Guardrails.
* **Phase 3 (Weeks 5-6):** IoT Gateway implementation and Calendar API sync.
* **Phase 4 (Weeks 7-8):** Frontend Portal development and User Acceptance Testing (UAT).

## 15\. Open Questions \& Risks

* **IoT Reliability:** How does the system handle sensor failures or false negatives in occupancy?
* **Policy Complexity:** Can the AI accurately interpret highly nuanced or unwritten departmental "gentleman's agreements"?
* **LLM Latency:** Will real-time negotiation between agents introduce delays in the user interface?

