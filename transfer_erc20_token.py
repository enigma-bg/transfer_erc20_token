import asyncio
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.exceptions import TransactionNotFound
import json

rpc_url = 'https://rpc.ankr.com/arbitrum'
explorer_url = 'https://arbiscan.io/'

w3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))

with open("erc20.json", "r") as abi_file:
    ERC20_ABI = json.load(abi_file)

CONTRACT_ADDRESS = "0xaf88d065e77c8cc2239327c5edb3a432268e5831"
CHECKSUM_CONTRACT_ADDRESS = w3.to_checksum_address(CONTRACT_ADDRESS)

TOKEN_CONTRACT = w3.eth.contract(address=CHECKSUM_CONTRACT_ADDRESS, abi=ERC20_ABI)


async def get_balance(address):
    balance = await TOKEN_CONTRACT.functions.balanceOf(address).call()
    decimals = await TOKEN_CONTRACT.functions.decimals().call()
    balance_in_units = balance / (10 ** decimals)
    return balance_in_units

async def send_erc20_transaction(
    sender_private_key, sender_address, receiver_address, amount, gas_multiplier=1.2
):

    decimals = await TOKEN_CONTRACT.functions.decimals().call()
    amount_in_wei = int(amount * (10 ** decimals))
    sender_balance = await TOKEN_CONTRACT.functions.balanceOf(sender_address).call()
    sender_balance_decimal = sender_balance / (10 ** decimals)
    receiver_balance = await TOKEN_CONTRACT.functions.balanceOf(receiver_address).call()

    print(f"Баланс отправителя до транзакции: {sender_balance_decimal}")
    print(f"Баланс получателя до транзакции: {receiver_balance / (10 ** decimals)}")

    if sender_balance < amount_in_wei:
        print(f"Недостаточно токенов для выполнения транзакции. Баланс: {sender_balance_decimal} токенов.")
        return

    nonce = await w3.eth.get_transaction_count(sender_address)
    gas_price = await w3.eth.gas_price
    gas_estimate = await TOKEN_CONTRACT.functions.transfer(receiver_address, amount_in_wei).estimate_gas({"from": sender_address})

    transaction = await TOKEN_CONTRACT.functions.transfer(receiver_address, amount_in_wei).build_transaction(
        {
            "chainId": await w3.eth.chain_id,
            "nonce": nonce,
            "gas": int(gas_estimate * gas_multiplier),
            "gasPrice": int(gas_price),
        }
    )

    signed_tx = w3.eth.account.sign_transaction(transaction, sender_private_key)
    print("Транзакция подписана!")

    tx_hash = await w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Транзакция отправлена! Хеш: {w3.to_hex(tx_hash)}")

    print("Ожидание подтверждения транзакции...")
    receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
    print("Транзакция подтверждена!", receipt)

    sender_balance_after = await get_balance(sender_address)
    receiver_balance_after = await get_balance(receiver_address)

    print(f"Баланс отправителя после транзакции: {sender_balance_after}")
    print(f"Баланс получателя после транзакции: {receiver_balance_after}")

async def main():
    sender_private_key = input("Введите приватный ключ отправителя: ").strip()
    sender_address = w3.eth.account.from_key(sender_private_key).address
    receiver_address = input("Введите адрес получателя: ").strip()
    amount = float(input("Введите количество токенов для отправки: "))

    print(f"Отправитель: {sender_address}")
    print(f"Получатель: {receiver_address}")
    print(f"Сумма для отправки: {amount}")

    await send_erc20_transaction(sender_private_key, sender_address, receiver_address, amount)


if __name__ == "__main__":
    asyncio.run(main())
