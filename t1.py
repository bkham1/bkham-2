    client = Client(api_key=API_KEY, socket_enabled=False)

    try:
        await login(client)
    except Exception:
        return

    print(colorize("جاري تحليل رابط المجتمع للحصول على المعرّف...", "*"))
    try:
        link_data = await client.get_from_code(TARGET_COMMUNITY_LINK)
        target_com_id = getattr(link_data, 'comId', None)

        if not target_com_id:    
            print(f"\033[0;31m[FATAL ERROR]: لم يتم العثور على معرّف مجتمع (ComId).")    
            return

    except Exception as e:
        print(f"\033[0;31m[FATAL ERROR]: فشل في تحليل الرابط: {e}\033[0m")
        return

    sub_client = SubClient(comId=target_com_id, profile=client.profile)

    print(colorize(f"بدء بوت المراقبة للمجتمع: {target_com_id}", "✅"))
    await monitor_community(sub_client, target_com_id)

if __name__ == "__main__":
    try:
        run(main())
    except Exception as e:
        print(f"\033[0;31m[TERMINATED]: تم إيقاف البوت بسبب خطأ حاسم: {e}\033[0m")
