import discord
from discord.ext import commands
from discord import app_commands
from sms import SendSms
import asyncio
import threading
import time
from keep_alive import keep_alive
import os
from dotenv import load_dotenv

keep_alive()
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Sms servis metodlarını listele
servisler_sms = []
for attribute in dir(SendSms):
    attribute_value = getattr(SendSms, attribute)
    if callable(attribute_value) and not attribute.startswith("__"):
        servisler_sms.append(attribute)

PREMIUM_ROLE_ID = 1378504273083633785
ALLOWED_CHANNELS = [1378504347976990830, 1378526060718592020]
TICKET_ALLOWED_ROLE_ID = [1378504271083077642, 1378698053946445965]
TICKET_CATEGORY_ID = 1378650450605248542
aktif_gonderimler = {}


@bot.event
async def on_ready():
    print(f'{bot.user} Aktif!')
    try:
        synced = await bot.tree.sync()
        print(f"Slash komutları senkronize edildi: {len(synced)} komut.")
    except Exception as e:
        print(f"Slash komut senkronizasyon hatası: {e}")


async def turbo(interaction: discord.Interaction, telefon: str, sayi: int):
    user_id = interaction.user.id

    if user_id in aktif_gonderimler:
        await interaction.response.send_message(
            "🛑 Zaten bir gönderiminiz aktif!", ephemeral=False)
        msg = await interaction.original_response()
        await asyncio.sleep(5)
        await msg.delete()
        return

    if len(telefon) != 10 or not telefon.isdigit():
        await interaction.response.send_message("🛑 Telefon numarası geçersiz!",
                                                ephemeral=False)
        msg = await interaction.original_response()
        await asyncio.sleep(5)
        await msg.delete()
        return

    if sayi <= 0:
        await interaction.response.send_message("🛑 SMS sayısı pozitif olmalı!",
                                                ephemeral=False)
        msg = await interaction.original_response()
        await asyncio.sleep(5)
        await msg.delete()
        return

    member = interaction.guild.get_member(user_id)
    has_premium = PREMIUM_ROLE_ID in [role.id for role in member.roles]

    if not has_premium and sayi > 40:
        await interaction.response.send_message(
            f"🛑 <@&{PREMIUM_ROLE_ID}> üyesi değilsiniz. Max 40 SMS!",
            ephemeral=False)
        msg = await interaction.original_response()
        await asyncio.sleep(5)
        await msg.delete()
        return

    if has_premium and sayi > 150:
        await interaction.response.send_message(
            f"🛑 Premium üyeler en fazla 200 SMS gönderebilir.",
            ephemeral=False)
        msg = await interaction.original_response()
        await asyncio.sleep(5)
        await msg.delete()
        return

    embed_start = discord.Embed(title="discord.gg/yakında",
                                color=discord.Color.purple())
    embed_start.add_field(name="📶 Durum",
                          value="Gönderiliyor...",
                          inline=False)
    embed_start.add_field(name="👤 Gönderen",
                          value=f"{interaction.user.mention}",
                          inline=True)
    embed_start.add_field(name="💣 Miktar", value=f"{sayi}", inline=True)
    embed_start.add_field(
        name="⭐ Üyelik",
        value=f"<@&{PREMIUM_ROLE_ID}>" if has_premium else "Free",
        inline=True)
    embed_start.add_field(name="⏳ Kalan Üyelik Süresi",
                          value="Sınırsız",
                          inline=True)
    embed_start.set_image(url="https://i.postimg.cc/FH8x5Y1w/Sms.png")
    embed_start.set_footer(text="Made by scher4851 | discord.gg/yakında")

    await interaction.response.send_message(embed=embed_start)
    msg = await interaction.original_response()

    def turbo_gonder():
        sms = SendSms(telefon, "")
        sent_count = 0
        hedef_adet = int(sayi * 1.5)

        while sent_count < hedef_adet:
            for servis in servisler_sms:
                if sent_count >= hedef_adet:
                    break
                try:
                    result = getattr(sms, servis)()
                    sent_count += 1
                    time.sleep(0.01)
                except Exception as e:
                    print(f"Hata: {e}")
                    sent_count += 1

        aktif_gonderimler.pop(user_id, None)

        embed_done = discord.Embed(title="discord.gg/yakında",
                                   color=discord.Color.purple())
        embed_done.add_field(name="📶 Durum", value="Gönderildi", inline=False)
        embed_done.add_field(name="👤 Gönderen",
                             value=f"{interaction.user.mention}",
                             inline=True)
        embed_done.add_field(name="💣 Miktar", value=f"{sayi}",
                             inline=True)  # Kullanıcıya gerçek sayı
        embed_done.add_field(
            name="⭐ Üyelik",
            value=f"<@&{PREMIUM_ROLE_ID}>" if has_premium else "Free",
            inline=True)
        embed_done.add_field(name="⏳ Kalan Üyelik Süresi",
                             value="Sınırsız",
                             inline=True)
        embed_done.set_image(url="https://i.postimg.cc/FH8x5Y1w/Sms.png")
        embed_done.set_footer(text="Made by scher4851 | discord.gg/yakında")

        async def mesaj_sil():
            try:
                await msg.edit(embed=embed_done)
                await asyncio.sleep(10)
                await msg.delete()
            except Exception:
                pass

        asyncio.run_coroutine_threadsafe(mesaj_sil(), bot.loop)

    thread = threading.Thread(target=turbo_gonder, daemon=True)
    aktif_gonderimler[user_id] = thread
    thread.start()


@bot.tree.command(name="sms", description="Turbo SMS gönderimini başlatır.")
@app_commands.describe(telefon="Telefon numarası (10 haneli)",
                       sayi="Gönderilecek SMS sayısı")
async def slash_turbo(interaction: discord.Interaction, telefon: str,
                      sayi: int):
    if interaction.channel.id not in ALLOWED_CHANNELS:
        await interaction.response.send_message(
            "🛑 Bu komutu sadece belirli kanallarda kullanabilirsin.",
            ephemeral=True)
        return

    await turbo(interaction, telefon, sayi)


class TicketResponseButtons(discord.ui.View):

    def __init__(self, label: str, ticket_owner: discord.Member):
        super().__init__(timeout=None)
        self.label = label
        self.ticket_owner = ticket_owner

        if label.lower() == "satın alım":
            self.add_item(self.SatinAlindiButton(self))
            self.add_item(self.SatinAlinmadiButton(self))
        else:
            self.add_item(self.OnaylandiButton(self))
            self.add_item(self.OnaylanmadiButton(self))

    async def interaction_check(self,
                                interaction: discord.Interaction) -> bool:
        has_permission = any(role.id in TICKET_ALLOWED_ROLE_ID
                             for role in interaction.user.roles)
        if not has_permission:
            await interaction.response.send_message(
                "❌ Bu butona tıklamak için yetkin yok!", ephemeral=True)
            return False
        return True

    class SatinAlindiButton(discord.ui.Button):

        def __init__(self, parent):
            super().__init__(label="Satın Alındı",
                             style=discord.ButtonStyle.gray,
                             custom_id="satinalindi")
            self.parent = parent

        async def callback(self, interaction: discord.Interaction):
            role_id = 1378504273083633785  # Premium rol ID
            user = self.parent.ticket_owner
            guild = interaction.guild
            role = guild.get_role(role_id)

            # Rol ver
            if role:
                await user.add_roles(role)

            # Kanalda bilgi mesajı gönder
            await interaction.channel.send(
                "✅ Satın alım tamamlandı! 20 saniye sonra kapatılacak.")

            # Log kanalına gönder
            await self.send_log(interaction, satin_alindi=True)

            # 20 saniye sonra kanalı sil
            await asyncio.sleep(20)
            await interaction.channel.delete()

        async def send_log(self, interaction: discord.Interaction,
                           satin_alindi: bool):
            log_channel_id = 1378504325571022880
            guild = interaction.guild
            log_channel = guild.get_channel(log_channel_id)
            if not log_channel:
                return

            embed = discord.Embed(title="🧾 Satın Alım Durumu",
                                  color=discord.Color.green()
                                  if satin_alindi else discord.Color.red(),
                                  timestamp=discord.utils.utcnow())
            embed.add_field(name="Ticket Sahibi",
                            value=f"{self.parent.ticket_owner.mention}",
                            inline=False)
            embed.add_field(name="Durum", value="Satın Alındı ✅", inline=True)
            embed.add_field(name="Yetkili",
                            value=interaction.user.mention,
                            inline=True)
            embed.set_footer(text="Made by scher4851")

            await log_channel.send(embed=embed)

    class SatinAlinmadiButton(discord.ui.Button):

        def __init__(self, parent):
            super().__init__(label="Satın Alınmadı",
                             style=discord.ButtonStyle.gray,
                             custom_id="satinalinmadi")
            self.parent = parent

        async def callback(self, interaction: discord.Interaction):
            await interaction.channel.send(
                "❌ Satın Alım Kapatıldı! 20 saniye sonra kapanacak.")
            await self.send_log(interaction, satin_alindi=False)
            await asyncio.sleep(20)
            await interaction.channel.delete()

        async def send_log(self, interaction: discord.Interaction,
                           satin_alindi: bool):
            log_channel_id = 1378504325571022880
            guild = interaction.guild
            log_channel = guild.get_channel(log_channel_id)
            if not log_channel:
                return

            embed = discord.Embed(title="🧾 Satın Alım Durumu",
                                  color=discord.Color.red(),
                                  timestamp=discord.utils.utcnow())
            embed.add_field(name="Ticket Sahibi",
                            value=f"{self.parent.ticket_owner.mention}",
                            inline=False)
            embed.add_field(name="Durum",
                            value="Satın Alınmadı ❌",
                            inline=True)
            embed.add_field(name="Yetkili",
                            value=interaction.user.mention,
                            inline=True)
            embed.set_footer(text="Made by scher4851")

            await log_channel.send(embed=embed)

    class OnaylandiButton(discord.ui.Button):

        def __init__(self, parent):
            super().__init__(label="Onaylandı",
                             style=discord.ButtonStyle.gray,
                             custom_id="onaylandi")
            self.parent = parent

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_message("✅ Talep onaylandı.",
                                                    ephemeral=True)
            await interaction.channel.send(
                "✅ Talep Onaylandı! 20 saniye sonra kanal kapanacak.")
            await self.send_log(interaction, approved=True)
            await asyncio.sleep(20)
            await interaction.channel.delete()

        async def send_log(self, interaction: discord.Interaction,
                           approved: bool):
            log_channel_id = 1378504325571022880
            guild = interaction.guild
            log_channel = guild.get_channel(log_channel_id)
            if not log_channel:
                return

            embed = discord.Embed(title="🎫 Ticket Onay Durumu",
                                  color=discord.Color.green(),
                                  timestamp=discord.utils.utcnow())
            embed.add_field(
                name="Ticket Sahibi",
                value=
                f"{self.parent.ticket_owner.mention} ({self.parent.ticket_owner})",
                inline=False)
            embed.add_field(name="Talep Türü",
                            value=self.parent.label,
                            inline=False)
            embed.add_field(name="Durum", value="Onaylandı ✅", inline=False)
            embed.add_field(name="Onaylayan Yetkili",
                            value=interaction.user.mention,
                            inline=False)
            embed.set_footer(text="Made by scher4851")

            await log_channel.send(embed=embed)


class OnaylanmadiButton(discord.ui.Button):

    def __init__(self, parent):
        super().__init__(label="Onaylanmadı",
                         style=discord.ButtonStyle.gray,
                         custom_id="onaylanmadi")
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("❌ Talep onaylanmadı.",
                                                ephemeral=True)
        await interaction.channel.send(
            "❌ Talep Reddedildi! 20 saniye sonra kanal kapanacak.")
        await self.send_log(interaction, approved=False)
        await asyncio.sleep(20)
        await interaction.channel.delete()

    async def send_log(self, interaction: discord.Interaction, approved: bool):
        log_channel_id = 1378504325571022880
        guild = interaction.guild
        log_channel = guild.get_channel(log_channel_id)
        if not log_channel:
            return

        embed = discord.Embed(title="🎫 Ticket Onay Durumu",
                              color=discord.Color.red(),
                              timestamp=discord.utils.utcnow())
        embed.add_field(
            name="Ticket Sahibi",
            value=
            f"{self.parent.ticket_owner.mention} ({self.parent.ticket_owner})",
            inline=False)
        embed.add_field(name="Talep Türü",
                        value=self.parent.label,
                        inline=False)
        embed.add_field(name="Durum", value="Onaylanmadı ❌", inline=False)
        embed.add_field(name="Onaylayan Yetkili",
                        value=interaction.user.mention,
                        inline=False)
        embed.set_footer(text="Made by scher4851")

        await log_channel.send(embed=embed)


@bot.tree.command(name="ticket",
                  description="Satın alım veya destek için ticket oluştur.")
async def ticket_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="scher4851 Developers!",
        description=
        "Satın alım veya destek için aşağıdan bir ticket oluşturabilirsiniz.",
        color=discord.Color.purple())
    embed.set_footer(text="Made by: scher4851")

    view = TicketOptionButtons(interaction.user)
    await interaction.response.send_message(embed=embed, view=view)


class TicketOptionButtons(discord.ui.View):

    def __init__(self, user: discord.Member):
        super().__init__(timeout=None)
        self.user = user
        self.add_item(self.TicketButton("Satın Alım"))
        self.add_item(self.TicketButton("Destek"))

    class TicketButton(discord.ui.Button):

        def __init__(self, tur):
            super().__init__(label=tur,
                             style=discord.ButtonStyle.gray)  # Buton rengi gri
            self.tur = tur.lower()

        async def callback(self, interaction: discord.Interaction):
            guild = interaction.guild
            category = discord.utils.get(guild.categories,
                                         id=TICKET_CATEGORY_ID)

            if not category:
                await interaction.response.send_message(
                    "❌ Ticket kategorisi bulunamadı.", ephemeral=True)
                return

            ticket_name = f"ticket-{interaction.user.name}"
            existing = discord.utils.get(guild.channels, name=ticket_name)

            if existing:
                await interaction.response.send_message(
                    f"❌ Zaten açık bir ticketın var: {existing.mention}",
                    ephemeral=True)
                return

            overwrites = {
                guild.default_role:
                discord.PermissionOverwrite(read_messages=False),
                interaction.user:
                discord.PermissionOverwrite(read_messages=True,
                                            send_messages=True),
            }
            yetkili_rol = discord.utils.get(guild.roles,
                                            id=TICKET_ALLOWED_ROLE_ID)
            if yetkili_rol:
                overwrites[yetkili_rol] = discord.PermissionOverwrite(
                    read_messages=True, send_messages=True)

            channel = await guild.create_text_channel(
                name=ticket_name,
                category=category,
                overwrites=overwrites,
                topic=f"{interaction.user} - {self.tur}")

            view = TicketResponseButtons(self.tur, interaction.user)

            # Gömülü karşılama mesajı
            embed_ticket = discord.Embed(
                description=
                f"Merhaba {interaction.user.mention}, talebiniz kaydedildi.",
                color=discord.Color.dark_gray())
            await channel.send(embed=embed_ticket, view=view)
            await interaction.response.send_message(
                f"✅ Ticket oluşturuldu: {channel.mention}", ephemeral=True)


class SatinAlindiButton(discord.ui.Button):

    def __init__(self, parent):
        super().__init__(label="Satın Alındı",
                         style=discord.ButtonStyle.gray,
                         custom_id="satinalindi")
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        role_id = 1378504273083633785
        user = self.parent.ticket_owner
        guild = interaction.guild
        role = guild.get_role(role_id)

        if role:
            await user.add_roles(role)

        await interaction.channel.send(
            "✅ Satın alım tamamlandı! 20 saniye sonra kapatılacak.")

        await asyncio.sleep(20)
        await interaction.channel.delete()

bot.run(os.getenv("TOKEN"))
