import { NextResponse } from 'next/server';
import * as fs from 'fs';
import * as path from 'path';

const NERVE_CENTER = path.join(process.cwd(), '..', '..', 'nerve_center');
const CONTACTS_FILE = path.join(NERVE_CENTER, 'crm', 'contacts.json');

interface Contact {
  id: string;
  name: string;
  email: string;
  company: string;
  type: string;
  status: string;
  is_vip: boolean;
  lead_stage?: string;
  lead_value?: number;
  created_at: string;
}

function loadContacts(): Contact[] {
  try {
    if (fs.existsSync(CONTACTS_FILE)) {
      const content = fs.readFileSync(CONTACTS_FILE, 'utf-8');
      return JSON.parse(content);
    }
  } catch (error) {
    console.error('Error loading contacts:', error);
  }
  return [];
}

function saveContacts(contacts: Contact[]): boolean {
  try {
    const dir = path.dirname(CONTACTS_FILE);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(CONTACTS_FILE, JSON.stringify(contacts, null, 2));
    return true;
  } catch (error) {
    console.error('Error saving contacts:', error);
    return false;
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { name, email, company, type } = body;

    if (!name || !email) {
      return NextResponse.json(
        { error: 'Name and email are required' },
        { status: 400 }
      );
    }

    const contacts = loadContacts();

    // Check for duplicate email
    if (contacts.some(c => c.email.toLowerCase() === email.toLowerCase())) {
      return NextResponse.json(
        { error: 'Contact with this email already exists' },
        { status: 400 }
      );
    }

    const newContact: Contact = {
      id: `contact_${Date.now()}`,
      name,
      email,
      company: company || '',
      type: type || 'lead',
      status: 'active',
      is_vip: false,
      lead_stage: type === 'lead' ? 'new' : undefined,
      lead_value: type === 'lead' ? 0 : undefined,
      created_at: new Date().toISOString(),
    };

    contacts.push(newContact);

    if (saveContacts(contacts)) {
      return NextResponse.json({
        success: true,
        contact: newContact,
        message: 'Contact added successfully',
      });
    } else {
      return NextResponse.json(
        { error: 'Failed to save contact' },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error('Contacts API error:', error);
    return NextResponse.json(
      { error: 'Failed to add contact' },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    const contacts = loadContacts();
    return NextResponse.json({ contacts });
  } catch (error) {
    console.error('Get contacts error:', error);
    return NextResponse.json({ contacts: [] });
  }
}
