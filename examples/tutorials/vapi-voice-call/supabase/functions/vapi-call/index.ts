import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import { Client } from "npm:@modelcontextprotocol/sdk@1.12.1/client/index.js";
import { StreamableHTTPClientTransport } from "npm:@modelcontextprotocol/sdk@1.12.1/client/streamableHttp.js";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Max-Age": "86400",
};

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    // Parse request body
    const body = await req.json();
    const { name, email, phone, interests } = body;

    // Format phone number to E.164 (+1 for US if 10 digits)
    let formattedPhone = (phone || "").replace(/\D/g, "");
    if (formattedPhone.length === 10) {
      formattedPhone = `+1${formattedPhone}`;
    } else if (formattedPhone.length === 11 && formattedPhone.startsWith("1")) {
      formattedPhone = `+${formattedPhone}`;
    } else if (!formattedPhone.startsWith("+")) {
      formattedPhone = `+${formattedPhone}`;
    }

    // MCP server config from secrets
    const mcpServerUrl = Deno.env.get("MCP_QUALIFY_SERVER_URL");
    const mcpAuthToken = Deno.env.get("MCP_QUALIFY_AUTH_TOKEN");

    if (!mcpServerUrl) {
      return new Response(
        JSON.stringify({ error: "Missing MCP_QUALIFY_SERVER_URL secret" }),
        { status: 500, headers: corsHeaders }
      );
    }

    // Set up MCP client
    const client = new Client(
      {
        name: "streamable-http-client",
        version: "1.0.0",
      },
      {
        capabilities: {},
      }
    );

    const baseUrl = new URL(mcpServerUrl);
    const transportOptions = {
      requestInit: {
        headers: {} as Record<string, string>,
      },
    };
    if (mcpAuthToken) {
      transportOptions.requestInit.headers.Authorization = `Bearer ${mcpAuthToken}`;
    }
    const transport = new StreamableHTTPClientTransport(baseUrl, transportOptions);

    await client.connect(transport);

    // Prepare arguments for Vapi create_call tool
    const args = {
      assistantId: "b55dd788-194b-4550-a288-d5fbca2be46b",
      phoneNumberId: "85ebc4fd-d81c-4dac-9c15-f032ca4ca698",
      customer: {
        phoneNumber: formattedPhone,
        name,
        email,
        interests,
      },
    };

    // Call the Vapi create_call tool via MCP
    const result = await client.callTool({
      name: "create_call",
      arguments: args,
    });

    await client.close();

    if (result.isError) {
      return new Response(
        JSON.stringify({ error: result.content }),
        { status: 500, headers: corsHeaders }
      );
    }

    return new Response(
      JSON.stringify({ success: true, data: result.content }),
      { status: 200, headers: corsHeaders }
    );
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message || error.toString() }),
      { status: 500, headers: corsHeaders }
    );
  }
});
