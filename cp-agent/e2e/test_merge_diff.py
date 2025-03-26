import pytest

from cp_agent.utils.merge_diff import merge_diff


@pytest.mark.asyncio
async def test_merge_shadcn_component() -> None:
    original_code = """import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Form } from "@/components/ui/form"

export function DatePickerForm() {
  const form = useForm()

  return (
    <Form {...form}>
      <Button>Pick a date</Button>
    </Form>
  )
}"""

    diff_content = """import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Form } from "@/components/ui/form"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { format } from "date-fns"
import { Calendar as CalendarIcon } from "lucide-react"

export function DatePickerForm() {
    // ...existing code...
    const [date, setDate] = useState<Date>();

    return (
        <Form {...form}>
            <Popover>
                <PopoverTrigger asChild>
                    <Button variant="outline">
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {date ? format(date, "PPP") : <span>Pick a date</span>}
                    </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                        mode="single"
                        selected={date}
                        onSelect={setDate}
                        initialFocus
                    />
                </PopoverContent>
            </Popover>
        </Form>
    )
}"""

    merged_code, success = await merge_diff(original_code, diff_content)
    assert success
    assert "PopoverTrigger" in merged_code
    assert "date-fns" in merged_code
    assert "CalendarIcon" in merged_code
    assert 'variant="outline"' in merged_code


@pytest.mark.asyncio
async def test_merge_supabase_client() -> None:
    original_code = """import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
)

export async function getUser() {
  const { data: { user } } = await supabase.auth.getUser()
  return user
}"""

    diff_content = """import { createClient } from '@supabase/supabase-js'
import { Database } from '@/types/supabase'

// ...existing code...

export async function getUser() {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return null;

    const { data: profile } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', user.id)
        .single();

    return {
        ...user,
        profile
    }
}

export async function updateProfile({
    username,
    avatar_url
}: {
    username: string;
    avatar_url?: string;
}) {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) throw new Error('Not authenticated');

    const { data, error } = await supabase
        .from('profiles')
        .update({
            username,
            avatar_url,
            updated_at: new Date().toISOString(),
        })
        .eq('id', user.id);

    if (error) throw error;
    return data;
}"""

    merged_code, success = await merge_diff(original_code, diff_content)
    assert success
    assert "Database" in merged_code
    assert "profiles" in merged_code
    assert "updateProfile" in merged_code
    assert "avatar_url?" in merged_code


@pytest.mark.asyncio
async def test_merge_react_component() -> None:
    original_code = """'use client'

import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'

export function LoginButton() {
  const router = useRouter()

  return (
    <Button onClick={() => router.push('/login')}>
      Login
    </Button>
  )
}"""

    diff_content = """'use client'

import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Session } from '@supabase/supabase-js'
import { useEffect } from 'react'

interface LoginButtonProps {
    session: Session | null;
    className?: string;
}

export function LoginButton({ session, className }: LoginButtonProps) {
    const router = useRouter();

    useEffect(() => {
        if (session) {
            router.refresh();
        }
    }, [session, router]);

    // ...existing code...
    return (
        <Button
            onClick={() => router.push('/login')}
            className={className}
            variant={session ? "outline" : "default"}
        >
            {session ? 'Dashboard' : 'Login'}
        </Button>
    )
}"""

    merged_code, success = await merge_diff(original_code, diff_content)
    assert success
    assert "Session" in merged_code
    assert "interface LoginButtonProps" in merged_code
    assert "useEffect" in merged_code
    assert "variant={session ?" in merged_code


@pytest.mark.asyncio
async def test_multiple_existing_code_marks() -> None:
    original_code = """import React from 'react'
import { useState } from 'react'

export function TodoList() {
    const [todos, setTodos] = useState([])
    const [input, setInput] = useState('')

    const addTodo = () => {
        if (input.trim()) {
            setTodos([...todos, input.trim()])
            setInput('')
        }
    }

    const removeTodo = (index) => {
        const newTodos = todos.filter((_, i) => i !== index)
        setTodos(newTodos)
    }

    return (
        <div>
            <div>
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Add todo"
                />
                <button onClick={addTodo}>Add</button>
            </div>
            <ul>
                {todos.map((todo, index) => (
                    <li key={index}>
                        {todo}
                        <button onClick={() => removeTodo(index)}>Delete</button>
                    </li>
                ))}
            </ul>
        </div>
    )
}"""

    diff_content = """import React from 'react'
import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'

export function TodoList() {
    // ...existing code...

    const [loading, setLoading] = useState(false)

    useEffect(() => {
        // Load saved todos
        const savedTodos = localStorage.getItem('todos')
        if (savedTodos) {
            setTodos(JSON.parse(savedTodos))
        }
    }, [])

    // ...existing code...

    const saveTodos = () => {
        setLoading(true)
        localStorage.setItem('todos', JSON.stringify(todos))
        setTimeout(() => setLoading(false), 500)
    }

    return (
        <Card className="w-[400px]">
            <CardContent className="p-4">
                <div className="space-y-4">
                    <div className="flex gap-2">
                        <Input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Add todo"
                            onKeyPress={(e) => e.key === 'Enter' && addTodo()}
                        />
                        <Button onClick={addTodo}>Add</Button>
                    </div>
                    <ul className="space-y-2">
                        {todos.map((todo, index) => (
                            <li key={index} className="flex justify-between items-center">
                                <span>{todo}</span>
                                <Button
                                    variant="destructive"
                                    size="sm"
                                    onClick={() => removeTodo(index)}
                                >
                                    Delete
                                </Button>
                            </li>
                        ))}
                    </ul>
                    <Button
                        className="w-full"
                        variant="outline"
                        onClick={saveTodos}
                        disabled={loading}
                    >
                        {loading ? 'Saving...' : 'Save Todos'}
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}"""

    merged_code, success = await merge_diff(original_code, diff_content)
    assert success
    # Verify new imports were added
    assert "useEffect" in merged_code
    assert "Button" in merged_code
    assert "Card" in merged_code
    # Verify original state and handlers were preserved
    assert "const [todos, setTodos] = useState([])" in merged_code
    assert "const [input, setInput] = useState('')" in merged_code
    assert "const addTodo = () =>" in merged_code
    assert "const removeTodo = (index) =>" in merged_code
    # Verify new features were added
    assert "const [loading, setLoading] = useState(false)" in merged_code
    assert "localStorage.getItem('todos')" in merged_code
    assert "const saveTodos = () =>" in merged_code
    assert 'variant="destructive"' in merged_code


@pytest.mark.asyncio
async def test_merge_api_route() -> None:
    original_code = """import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  const requestUrl = new URL(request.url)
  const supabase = createRouteHandlerClient({ cookies })

  await supabase.auth.signOut()

  return NextResponse.redirect(requestUrl.origin, {
    status: 301,
  })
}"""

    diff_content = """import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

export async function POST(request: Request) {
    try {
        const supabase = createRouteHandlerClient({ cookies });
        const {
            data: { session },
        } = await supabase.auth.getSession();

        if (!session) {
            return NextResponse.json(
                { error: 'Unauthorized' },
                { status: 401 }
            );
        }

        await supabase.auth.signOut();

        // ...existing code...
        return NextResponse.json({ success: true });
    } catch (error) {
        return NextResponse.json(
            { error: 'Internal Server Error' },
            { status: 500 }
        );
    }
}"""

    merged_code, success = await merge_diff(original_code, diff_content)
    assert success
    assert "dynamic = 'force-dynamic'" in merged_code
    assert "getSession" in merged_code
    assert "Unauthorized" in merged_code
    assert "Internal Server Error" in merged_code
