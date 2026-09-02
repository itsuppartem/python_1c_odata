"""Register virtual tables: SliceLast is information-only; accumulation uses Balance/Turnovers."""

from python_1c_odata import AccumulationRegister, CalculationRegister, InformationRegister


async def test_information_slice_last_named_params(fake_odata, infobase):
    fake_odata.respond(200, {"value": [{"Курс": 92.1}]})
    payload = await InformationRegister(infobase, "КурсыВалют").slice_last(
        period="2024-03-20T00:00:00",
        condition="Валюта_Key eq guid'aaa'",
        select="Период,Курс",
    )
    assert payload["value"][0]["Курс"] == 92.1
    req = fake_odata.last
    assert req["path"].endswith(
        "InformationRegister_КурсыВалют/SliceLast("
        "Period=datetime'2024-03-20T00:00:00',Condition='Валюта_Key eq guid'aaa'')"
    )
    assert "$select=Период,Курс" in req["query"]


async def test_information_slice_first(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    await InformationRegister(infobase, "КурсыВалют").slice_first()
    assert fake_odata.last["path"].endswith("InformationRegister_КурсыВалют/SliceFirst()")


async def test_information_record_type_suffix(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    await InformationRegister(infobase, "КурсыВалют", record_type=True).query(top=1)
    assert fake_odata.last["path"].endswith("InformationRegister_КурсыВалют_RecordType")


async def test_accumulation_balance(fake_odata, infobase):
    fake_odata.respond(200, {"value": [{"КоличествоBalance": 5}]})
    payload = await AccumulationRegister(infobase, "ТоварыНаСкладах").balance(
        period="2024-03-20T00:00:00",
        condition="Склад_Key eq guid'aaa'",
    )
    assert payload["value"][0]["КоличествоBalance"] == 5
    assert fake_odata.last["path"].endswith(
        "AccumulationRegister_ТоварыНаСкладах/Balance("
        "Period=datetime'2024-03-20T00:00:00',Condition='Склад_Key eq guid'aaa'')"
    )


async def test_accumulation_turnovers(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    await AccumulationRegister(infobase, "ТоварыНаСкладах").turnovers(
        start_period="2024-01-01T00:00:00",
        end_period="2024-02-01T00:00:00",
    )
    assert fake_odata.last["path"].endswith(
        "AccumulationRegister_ТоварыНаСкладах/Turnovers("
        "StartPeriod=datetime'2024-01-01T00:00:00',EndPeriod=datetime'2024-02-01T00:00:00')"
    )


async def test_accumulation_balance_and_turnovers(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    await AccumulationRegister(infobase, "ТоварыНаСкладах").balance_and_turnovers(
        start_period="2024-01-01T00:00:00",
        end_period="2024-02-01T00:00:00",
        condition="Склад_Key eq guid'aaa'",
    )
    assert fake_odata.last["path"].endswith(
        "AccumulationRegister_ТоварыНаСкладах/BalanceAndTurnovers("
        "StartPeriod=datetime'2024-01-01T00:00:00',"
        "EndPeriod=datetime'2024-02-01T00:00:00',"
        "Condition='Склад_Key eq guid'aaa'')"
    )


async def test_accumulation_has_no_slice_last():
    assert not hasattr(AccumulationRegister, "slice_last")


async def test_calculation_register_query_prefix(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    await CalculationRegister(infobase, "Начисления").query(top=1)
    assert fake_odata.last["path"].endswith("CalculationRegister_Начисления")


async def test_calculation_schedule_data(fake_odata, infobase):
    fake_odata.respond(200, {"value": [{"Дней": 5}]})
    payload = await CalculationRegister(infobase, "Начисления").schedule_data(
        condition="Recorder_Key eq guid'aaa'",
        select="Дней",
    )
    assert payload["value"][0]["Дней"] == 5
    assert fake_odata.last["path"].endswith(
        "CalculationRegister_Начисления/ScheduledData(Condition='Recorder_Key eq guid'aaa'')"
    )
    assert "$select=Дней" in fake_odata.last["query"]


async def test_calculation_actual_action_period(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    await CalculationRegister(infobase, "Начисления").actual_action_period()
    assert fake_odata.last["path"].endswith("CalculationRegister_Начисления/ActualActionPeriod()")


async def test_calculation_recalculation(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    await CalculationRegister(infobase, "Начисления").recalculation(
        condition="Recorder_Key eq guid'aaa'",
    )
    assert fake_odata.last["path"].endswith(
        "CalculationRegister_Начисления/Recalculation(Condition='Recorder_Key eq guid'aaa'')"
    )


async def test_calculation_base_named_params(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    await CalculationRegister(infobase, "Начисления").base(
        condition="ФизЛицо_Key eq guid'aaa'",
        main_register_dimensions="ФизЛицо,Организация",
        base_register_dimensions="Сотрудник,Организация",
        view_points="Результат",
        select="РезультатBase",
    )
    assert fake_odata.last["path"].endswith(
        "CalculationRegister_Начисления/Base("
        "Condition='ФизЛицо_Key eq guid'aaa'',"
        "MainRegisterDimensions='ФизЛицо,Организация',"
        "BaseRegisterDimensions='Сотрудник,Организация',"
        "ViewPoints='Результат')"
    )
    assert "$select=РезультатBase" in fake_odata.last["query"]


async def test_information_get_composite_key_wraps_uuid(fake_odata, infobase):
    fake_odata.respond(200, {"Курс": 92.1})
    payload = await InformationRegister(infobase, "КурсыВалют", record_type=True).get(
        {
            "Валюта_Key": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "Period": "datetime'2024-03-20T00:00:00'",
        }
    )
    assert payload["Курс"] == 92.1
    assert fake_odata.last["path"].endswith(
        "InformationRegister_КурсыВалют_RecordType("
        "Валюта_Key=guid'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',"
        "Period=datetime'2024-03-20T00:00:00')"
    )
