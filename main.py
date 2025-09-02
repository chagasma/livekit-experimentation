import asyncio
import os
from typing import Annotated
from livekit.agents import Agent, AgentSession, JobContext, RunContext, WorkerOptions, cli, function_tool
from livekit.plugins import deepgram, openai, cartesia, silero
import logging

# Configure seu contexto similar ao CallContext
class CommunicationContext:
    def __init__(self):
        self.call_ended = False
        self.call_input_paused = False
        self.client_audio_buffer = []
        self.message_history = []
        self.partner_id = "SIM"  # ou outro
        self.correct_answer = "código correto"
        self.panic_answer = "emergência"

# Equivalente ao check_answer do seu sistema
@function_tool
async def check_answer(
    ctx: RunContext,
    user_response: Annotated[str, "Resposta do usuário para verificação"],
) -> str:
    """Verifica se a resposta do cliente contém palavras-chave de segurança"""
    
    # Simula sua lógica tripla de verificação
    print(f"Verificando resposta: {user_response}")
    
    context = ctx.session.get_user_data("context")
    
    if context.correct_answer.lower() in user_response.lower():
        context.message_history.append({"role": "system", "content": "Resposta correta verificada"})
        return "Resposta de verificação confirmada. Cliente autenticado."
    
    if context.panic_answer.lower() in user_response.lower():
        context.message_history.append({"role": "system", "content": "Código de pânico detectado"})
        return "Código de emergência detectado. Escalando para manager."
    
    return "Resposta não reconhecida. Por favor, repita a palavra-chave de verificação."

# Equivalente ao talk_to_manager
@function_tool
async def talk_to_manager(
    ctx: RunContext,
    message: Annotated[str, "Mensagem para enviar ao manager"],
) -> str:
    """Comunica com o manager e aguarda resposta"""
    
    print(f"Enviando para manager: {message}")
    
    # Simula comunicação com manager
    # Em produção, você integraria com seu sistema atual
    await asyncio.sleep(2)  # Simula delay de processamento
    
    # Resposta simulada do manager
    manager_response = f"Manager recebido: {message}. Prossiga conforme protocolo."
    
    return manager_response

# Equivalente ao collect_feedback  
@function_tool
async def collect_feedback(
    ctx: RunContext,
    rating: Annotated[str, "Avaliação do atendimento (1-5 estrelas ou qualitativa)"],
) -> str:
    """Coleta feedback do cliente"""
    
    print(f"Feedback coletado: {rating}")
    
    context = ctx.session.get_user_data("context")
    context.message_history.append({"role": "feedback", "content": rating})
    
    return f"Obrigado pela avaliação: {rating}. Seu feedback é importante!"

# Agent principal - equivalente ao seu Communication Agent
class AuriaVoiceAgent(Agent):
    def __init__(self):
        # Prompt similar ao seu sistema com Jinja2
        partner_style = "informal e descontraído" if os.getenv("PARTNER_ID") == "SIM" else "formal e profissional"
        
        instructions = f"""
        Você é um agente da Auria Security, especializado em comunicação telefônica com clientes.
        
        Personalidade: {partner_style}
        
        Suas responsabilidades:
        1. Verificar identidade do cliente usando a ferramenta check_answer
        2. Resolver problemas ou escalar usando talk_to_manager quando necessário  
        3. Coletar feedback antes de encerrar
        
        IMPORTANTE:
        - Sempre seja educado e profissional
        - Use as ferramentas disponíveis quando apropriado
        - Mantenha conversas focadas no atendimento
        """
        
        super().__init__(
            instructions=instructions,
            tools=[check_answer, talk_to_manager, collect_feedback]
        )

async def entrypoint(ctx: JobContext):
    """Ponto de entrada - equivalente ao seu setup do Communication Agent"""
    
    # Setup inicial
    await ctx.connect()
    
    # Inicializa contexto
    communication_ctx = CommunicationContext()
    
    # Cria agente com providers flexíveis
    agent = AuriaVoiceAgent()
    
    # Configura pipeline de voz - VOCÊ CONTROLA CADA PEÇA
    session = AgentSession(
        # VAD para detectar fim de turno (igual seu sistema)
        vad=silero.VAD.load(),
        
        # STT - pode trocar por Deepgram, Azure, etc
        stt=deepgram.STT(model="nova-2"),
        
        # LLM - OpenAI, mas pode ser qualquer um
        llm=openai.LLM(model="gpt-4o-mini"),
        
        # TTS - usando Cartesia (mais barato) mas pode usar ElevenLabs
        tts=cartesia.TTS(voice="95856005-0332-41b6-9d65-6d67b0b9c462"),
        
        # Armazena contexto personalizado
        user_data={"context": communication_ctx}
    )
    
    # Inicia sessão
    await session.start(agent=agent, room=ctx.room)
    
    # Saudação inicial - equivalente ao seu prompt dinâmico
    greeting = "Olá, aqui é da Auria Security. Como posso ajudá-lo hoje?"
    await session.generate_reply(instructions=f"Cumprimente o cliente dizendo: {greeting}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        worker_type="agent",
    ))