# Document Signature Request Application

An enterprise internal workflow solution built on the Microsoft Power Platform to digitize, streamline, and automate document approval and e-signature processes.

---

## Overview

The **Document Signature Request** application simplifies and automates internal document signing. Developed using **Microsoft Power Apps** for the user interface and **Microsoft Power Automate** for backend workflow management, this system replaces manual paper routing with a sequential, traceable digital workflow.

---

## Tech Stack & Prerequisites

### Tech Stack

* **Frontend / UI:** Microsoft Power Apps


* **Workflow Engine:** Microsoft Power Automate


* **Document Repository:** Microsoft SharePoint Online


* **Email & Notifications:** Microsoft Outlook / Exchange


* **PDF Editor:** Adobe Acrobat Desktop



### Prerequisites

* Active Microsoft 365 enterprise account signed into Microsoft Edge and Outlook.


* Adobe Acrobat Desktop installed and set as the default application for `.pdf` files on client PCs.



---

## Architecture & Workflow

```text
[ Requester ]
     │
     ▼ Submits Request & PDF Attachment via Power Apps
[ Power Automate Flow ] ──► Copies File to SharePoint (/In Progress)
     │
     ▼ Sends Sequential Email with PDF Link
[ Approver 1..N ] ─────► Opens PDF in Adobe Acrobat App
     │                  ► Embeds Image Signature & Overwrites File in /In Progress
     │                  ► Clicks "Approve" in Email
     ▼
[ Final Decision ]
     ├─► Approved: File moved to /Approved folder + Summary email sent to Requester
     └─► Rejected: File moved to /Rejected folder + Notification email sent to Requester

```

### Detailed Workflow Steps

* **Initiation:** The requester submits a single merged PDF (content + signature page) in Power Apps, defines priority, adds details, and sets an ordered list of approvers.


* **File Processing:** Power Automate copies the attachment to `DOC_RELEASE/In Progress` and sends an email notification to the first approver.


* **Review & Signing:** The approver opens the PDF link in Adobe Acrobat Desktop, applies their signature image, and saves/overwrites the file directly back to the SharePoint `In Progress` folder.


* **Approval Confirmation:** The approver returns to Outlook and clicks **Approve** (or **Reject**). The workflow logs the timestamp and routes the task to the next approver.


* **Completion / Rejection:**
* **Approved:** The request status updates to `Signed`, the finalized PDF is archived in `DOC_RELEASE/Approved`, and a summary email is sent to the requester.


* **Rejected:** The process halts, moves the PDF to `DOC_RELEASE/Rejected`, and notifies the requester.





---

## SharePoint Directory Structure

The system manages documents across three lifecycle folders within SharePoint:

```text
Shared Documents/
└── 999_SHARE_VN/
    └── 290_IT/
        └── 200_IT_General/
            └── 0. DOC_RELEASE/
                ├── In Progress/  <-- Active documents awaiting approvals
                ├── Approved/     <-- Finalized, fully signed documents
                └── Rejected/     <-- Cancelled or rejected requests

```

---

## Key Features

* **Sequential Approval Engine:** Configurable recipient order for multi-stage sign-offs.


* **Real-Time Status Tracking:** Live status tracking (`Requested`, `In progress`, `Signed`, `Rejected`, `Canceled`).


* **Dashboard Controls:** Instant search by ID/Title, sorting by attributes (ID, Priority, Status, Date), and filtering options.


* **Request Cancellation:** Requesters can cancel pending requests with mandatory reason logging.


* **Automated Safety Reminders:** System alerts approvers if a document is signed on SharePoint but unconfirmed in email.



---

## User Guide

### Requesters

* **Access App:** Launch the Power Apps application from your portal.


* **Create Request:** Click **+ New document sign request**.


* **Fill Details:** Enter request title, attach a single merged PDF, select priority, and add details.


* **Set Approvers:** Enable sequential routing, list approver emails in order, and click **Send**.



### Approvers

* **Open Notification:** Locate the approval email titled `[RRC-IT_DocSign#{ID}]`.


* **Open File:** Click the document link and select **Edit** → **Open in App** (Adobe Acrobat).


* **Sign Document:** Place your signature image onto the document signature block.


* **Save File:** Save changes (`Ctrl + S`) to overwrite the original file in SharePoint.


* **Submit Action:** Return to Outlook and click **Approve** or **Reject**.



---

## Scope & Compliance

* **Internal Use Only:** Designed specifically for internal operational documents, work instructions, and company approvals.


* **Legal Compliance Note:** External contracts and government submissions require official Digital Signatures (Token/CA) per regulatory requirements.


 |
