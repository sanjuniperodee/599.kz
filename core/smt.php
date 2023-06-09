<?php
// Enter your code here, enjoy!

$secret_key = "B73EGLkDTTKuMiag";
$request = $requestForSignature = [
    'pg_order_id'=> $argv[1],
    'pg_merchant_id' => '545774',
    'pg_amount' => $argv[2],
    'pg_description' => 'test',
    'pg_salt' => 'ybeauty',
    'pg_success_url' => 'http://127.0.0.1:8000/successPayment/',
    'pg_failure_url'=> 'http://127.0.0.1:8000/checkout/',
    'pg_success_url_method'=> 'GET',
    'pg_failure_url_method'=> 'GET',
];

/**
 * Функция превращает многомерный массив в плоский
 */
function makeFlatParamsArray($arrParams, $parent_name = '')
{
    $arrFlatParams = [];
    $i = 0;
    foreach ($arrParams as $key => $val) {
        $i++;
        /**
         * Имя делаем вида tag001subtag001
         * Чтобы можно было потом нормально отсортировать и вложенные узлы не запутались при сортировке
         */
        $name = $parent_name . $key . sprintf('%03d', $i);
        if (is_array($val)) {
            $arrFlatParams = array_merge($arrFlatParams, makeFlatParamsArray($val, $name));
            continue;
        }
        $arrFlatParams += array($name => (string)$val);
    }

    return $arrFlatParams;
}

// Превращаем объект запроса в плоский массив
$requestForSignature = makeFlatParamsArray($requestForSignature);

// Генерация подписи
ksort($requestForSignature); // Сортировка по ключю
array_unshift($requestForSignature, 'init_payment.php'); // Добавление в начало имени скрипта
array_push($requestForSignature, $secret_key); // Добавление в конец секретного ключа

$request['pg_sig'] = md5(implode(';', $requestForSignature));

$myfile = fopen("core\\testfile.txt", "w");

fwrite($myfile, $request['pg_sig']);
fclose($myfile);